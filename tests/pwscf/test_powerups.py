import pytest

from atomate2.pwscf import powerups
from atomate2.pwscf.flows.core import DoubleRelaxMaker
from atomate2.pwscf.jobs.core import RelaxMaker
from atomate2.pwscf.sets.core import RelaxSetGenerator


@pytest.mark.parametrize(
    'powerup,attribute,settings',
    [
        ('update_user_control_settings', 'user_control', {'calculation': 'scf'}),
        ('update_user_kpoints_settings', 'user_kpoints', {'grid': (2, 2, 2)}),
        ('update_user_pseudos', 'user_pseudos', {'Si': 'Si.upf'}),
    ],
)
def test_update_user_settings(powerup, attribute, settings):
    powerup_func = getattr(powerups, powerup)

    # test maker
    rm = RelaxMaker(input_set_generator=RelaxSetGenerator())
    rm = powerup_func(rm, settings)
    for k, v in settings.items():
        assert getattr(rm.input_set_generator, attribute)[k] == v

    # test job
    job = RelaxMaker(input_set_generator=RelaxSetGenerator()).make(1)
    job = powerup_func(job, settings)
    for k, v in settings.items():
        assert getattr(job.function.__self__.input_set_generator, attribute)[k] == v

    # test flow maker
    drm = DoubleRelaxMaker(
        relax_maker1=RelaxMaker(input_set_generator=RelaxSetGenerator()),
        relax_maker2=RelaxMaker(input_set_generator=RelaxSetGenerator())
    )
    drm = powerup_func(drm, settings)
    for k, v in settings.items():
        assert getattr(drm.relax_maker1.input_set_generator, attribute)[k] == v
        assert getattr(drm.relax_maker2.input_set_generator, attribute)[k] == v

    # test flow
    drm = DoubleRelaxMaker(
        relax_maker1=RelaxMaker(input_set_generator=RelaxSetGenerator()),
        relax_maker2=RelaxMaker(input_set_generator=RelaxSetGenerator())
    )
    flow = drm.make(1)
    flow = powerup_func(flow, settings)
    for k, v in settings.items():
        assert getattr(flow.jobs[0].function.__self__.input_set_generator, attribute)[k] == v
        assert getattr(flow.jobs[1].function.__self__.input_set_generator, attribute)[k] == v

    # test name filter
    drm = DoubleRelaxMaker(
        relax_maker1=RelaxMaker(input_set_generator=RelaxSetGenerator(), name='relax 1'),
        relax_maker2=RelaxMaker(input_set_generator=RelaxSetGenerator(), name='relax 2')
    )
    flow = drm.make(1)
    flow = powerup_func(flow, settings, name_filter='relax 1')
    for k, v in settings.items():
        assert getattr(flow.jobs[0].function.__self__.input_set_generator, attribute)[k] == v
        assert getattr(flow.jobs[1].function.__self__.input_set_generator, attribute).get(k) != v


@pytest.mark.parametrize(
    'powerup, settings',
    [('add_metadata_to_flow', {'project': 'test'}), ('add_metadata_to_flow', {'a': 1, 'b': 2})],
)
def test_add_metadata_to_flow(powerup, settings):
    powerup_func = getattr(powerups, powerup)

    drm = DoubleRelaxMaker()
    flow = drm.make(1)
    flow = powerup_func(flow, settings)
    assert (
        flow.jobs[0].function.__self__.task_document_kwargs['additional_fields'] == settings
    )


@pytest.mark.parametrize('powerup, settings', [('update_pwscf_custodian_handlers', ())])
def test_update_pwscf_custodian_handlers(powerup, settings):
    powerup_func = getattr(powerups, powerup)

    drm = DoubleRelaxMaker()
    flow = drm.make(1)
    flow = powerup_func(flow, settings)
    # handlers are stored under run_pwscf_kwargs on the maker/job
    assert flow.jobs[0].function.__self__.run_pwscf_kwargs['handlers'] == settings
