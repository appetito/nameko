import pytest

from nameko.dependencies import Extension, Entrypoint, InjectionProvider
from nameko.testing.utils import get_dependency


class SimpleExtension(Extension):
    pass


class SimpleInjection(InjectionProvider):
    ext = SimpleExtension()


class SimpleEntrypoint(Entrypoint):
    pass

simple = SimpleEntrypoint.entrypoint


class Service(object):
    inj = SimpleInjection()

    @simple
    def meth1(self):
        pass

    @simple
    def meth2(self):
        pass


def test_entrypoint_uniqueness(container_factory):
    c1 = container_factory(Service, config={})
    c2 = container_factory(Service, config={})

    # entrypoint declarations are identical between containers
    c1_meth1_entrypoints = c1.service_cls.meth1.nameko_entrypoints
    c2_meth1_entrypoints = c2.service_cls.meth1.nameko_entrypoints
    assert c1_meth1_entrypoints == c2_meth1_entrypoints

    # entrypoint instances are different between containers
    c1_simple_meth1 = get_dependency(c1, SimpleEntrypoint, name="meth1")
    c2_simple_meth1 = get_dependency(c2, SimpleEntrypoint, name="meth1")
    assert c1_simple_meth1 != c2_simple_meth1

    # entrypoint instances are different within a container
    simple_meth1 = get_dependency(c1, SimpleEntrypoint, name="meth1")
    simple_meth2 = get_dependency(c1, SimpleEntrypoint, name="meth2")
    assert simple_meth1 != simple_meth2


def test_injection_uniqueness(container_factory):
    c1 = container_factory(Service, config={})
    c2 = container_factory(Service, config={})

    # injection declarations are identical between containers
    assert c1.service_cls.inj == c2.service_cls.inj

    # injection instances are different between containers
    inj1 = get_dependency(c1, SimpleInjection)
    inj2 = get_dependency(c2, SimpleInjection)
    assert inj1 != inj2


def test_extension_uniqueness(container_factory):
    c1 = container_factory(Service, config={})
    c2 = container_factory(Service, config={})
    inj1 = get_dependency(c1, SimpleInjection)
    inj2 = get_dependency(c2, SimpleInjection)

    # extension declarations are identical between containers
    assert c1.service_cls.inj.ext == c2.service_cls.inj.ext

    # extension instances are different between injections
    assert inj1 != inj2
    assert inj1.ext != inj2.ext


def test_clones_never_shared():

    ext = SimpleExtension(shared=True)
    assert ext._Extension__shared is True
    assert "shared" not in ext._Extension__state

    ext_clone = ext.clone()
    assert ext_clone._Extension__shared is False


def test_clones_marked_as_clones():

    ext = SimpleExtension()
    assert ext._Extension__clone is False
    ext_clone = ext.clone()
    assert ext_clone._Extension__clone is True


def test_clones_cannot_be_bound():

    ext = SimpleExtension()
    ext_clone = ext.clone()

    with pytest.raises(RuntimeError) as exc_info:
        ext_clone.bind("name", None)
    assert exc_info.value.message == "Cloned extensions cannot be bound."


def test_clones_cannot_be_cloned():

    ext = SimpleExtension()
    ext_clone = ext.clone()

    with pytest.raises(RuntimeError) as exc_info:
        ext_clone.clone()
    assert exc_info.value.message == "Cloned extensions cannot be cloned."


def test_require_super_init():

    class BrokenExtension(Extension):
        def __init__(self):
            pass

    ext = BrokenExtension()

    with pytest.raises(RuntimeError) as exc_info:
        ext.clone()
    assert "forget to call super().__init__()" in exc_info.value.message