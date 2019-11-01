import formencode
import itertools
import transaction

from csv import DictReader
from io import StringIO
from math import factorial
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config
from pywebtools.formencode import CSRFSchema, State, CSRFValidator
from pywebtools.pyramid.auth.views import current_user, require_permission
from pywebtools.pyramid.decorators import require_method
from pywebtools.sqlalchemy import DBSession
from sqlalchemy import and_, func

from ess.models import Experiment, DataSet, DataItem
from ess.validators import DynamicSchema, DataSetUniqueValidator, DataSetExistsValidator


def init(config):
    config.add_route('experiment.data', '/experiments/{eid}/data')
    config.add_route('experiment.data.create', '/experiments/{eid}/data/create')
    config.add_route('experiment.data.upload', '/experiments/{eid}/data/upload')
    config.add_route('experiment.data.view', '/experiments/{eid}/data/{did}')
    config.add_route('experiment.data.edit', '/experiments/{eid}/data/{did}/edit')
    config.add_route('experiment.data.delete', '/experiments/{eid}/data/{did}/delete')
    config.add_route('experiment.data.item.add', '/experiments/{eid}/data/{did}/add')
    config.add_route('experiment.data.item.reorder', '/experiments/{eid}/data/{did}/reorder')
    config.add_route('experiment.data.item.edit', '/experiments/{eid}/data/{did}/{diid}/edit')
    config.add_route('experiment.data.item.delete', '/experiments/{eid}/data/{did}/{diid}/delete')
    config.add_route('experiment.latinsquare', '/experiments/{eid}/latinsquares')
    config.add_route('experiment.latinsquare.create', '/experiments/{eid}/latinsquares/create')
    config.add_route('experiment.latinsquare.view', '/experiments/{eid}/latinsquares/{did}')
    config.add_route('experiment.latinsquare.edit', '/experiments/{eid}/latinsquares/{did}/edit')
    config.add_route('experiment.latinsquare.edit.estimate', '/experiments/{eid}/latinsquares/{did}/edit/estimate')
    config.add_route('experiment.latinsquare.delete', '/experiments/{eid}/latinsquares/{did}/delete')


@view_config(route_name='experiment.data', renderer='ess:templates/data/data_list.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='view')
def data_list(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Data Sets',
                            'url': request.route_url('experiment.data', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


class DataSetCreateSchema(CSRFSchema):

    name = DataSetUniqueValidator(not_empty=True)


@view_config(route_name='experiment.data.create', renderer='ess:templates/data/data_create.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def data_create(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        if request.method == 'POST':
            try:
                params = DataSetCreateSchema().to_python(request.params, State(request=request,
                                                                               dbsession=dbsession,
                                                                               experiment=experiment))
                with transaction.manager:
                    dbsession.add(experiment)
                    data_set = DataSet(name=params['name'],
                                       experiment=experiment,
                                       type='dataset')
                    data_set['columns'] = []
                    dbsession.add(data_set)
                dbsession.add(experiment)
                dbsession.add(data_set)
                raise HTTPFound(request.route_url('experiment.data.edit', eid=experiment.id, did=data_set.id))
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Data Sets',
                                    'url': request.route_url('experiment.data', eid=experiment.id)},
                                   {'title': 'Add',
                                    'url': request.route_url('experiment.data.create', eid=experiment.id)}],
                        'values': request.params,
                        'errors': e.error_dict}
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Data Sets',
                            'url': request.route_url('experiment.data', eid=experiment.id)},
                           {'title': 'Add',
                            'url': request.route_url('experiment.data.create', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


class DataSetUploadSchema(CSRFSchema):

    name = DataSetUniqueValidator(not_empty=True)
    source = formencode.validators.FieldStorageUploadConverter(not_empty=True)


@view_config(route_name='experiment.data.upload', renderer='ess:templates/data/data_upload.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def data_upload(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        if request.method == 'POST':
            try:
                params = DataSetUploadSchema().to_python(request.params, State(request=request,
                                                                               dbsession=dbsession,
                                                                               experiment=experiment))
                with transaction.manager:
                    dbsession.add(experiment)
                    data_set = DataSet(name=params['name'],
                                       experiment=experiment,
                                       type='dataset')
                    reader = DictReader(StringIO(params['source'].file.read().decode('utf-8')))
                    data_set['columns'] = reader.fieldnames
                    dbsession.add(data_set)
                    for idx, line in enumerate(reader):
                        item = DataItem(data_set=data_set,
                                        order=idx)
                        item['values'] = line
                        dbsession.add(item)
                dbsession.add(experiment)
                dbsession.add(data_set)
                raise HTTPFound(request.route_url('experiment.data.view', eid=experiment.id, did=data_set.id))
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Data Sets',
                                    'url': request.route_url('experiment.data', eid=experiment.id)},
                                   {'title': 'Upload',
                                    'url': request.route_url('experiment.data.upload', eid=experiment.id)}],
                        'values': request.params,
                        'errors': e.error_dict}
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Data Sets',
                            'url': request.route_url('experiment.data', eid=experiment.id)},
                           {'title': 'Upload',
                            'url': request.route_url('experiment.data.upload', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


class DataSetEditSchema(CSRFSchema):

    name = DataSetUniqueValidator(not_empty=True)
    column = formencode.foreach.ForEach(formencode.validators.UnicodeString())


@view_config(route_name='experiment.data.view', renderer='ess:templates/data/data_view.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def data_view(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    data_set = dbsession.query(DataSet).filter(and_(DataSet.id == request.matchdict['did'],
                                                    DataSet.experiment_id == request.matchdict['eid'],
                                                    DataSet.type == 'dataset')).first()
    if experiment and data_set:
        return {'experiment': experiment,
                'data_set': data_set,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Data Sets',
                            'url': request.route_url('experiment.data', eid=experiment.id)},
                           {'title': data_set.name,
                            'url': request.route_url('experiment.data.view', eid=experiment.id, did=data_set.id)}]}
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.data.edit', renderer='ess:templates/data/data_edit.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def data_edit(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    data_set = dbsession.query(DataSet).filter(and_(DataSet.id == request.matchdict['did'],
                                                    DataSet.experiment_id == request.matchdict['eid'],
                                                    DataSet.type == 'dataset')).first()
    if experiment and data_set:
        if request.method == 'POST':
            try:
                params = DataSetEditSchema().to_python(request.params, State(request=request,
                                                                             dbsession=dbsession,
                                                                             experiment=experiment,
                                                                             data_set=data_set))
                with transaction.manager:
                    dbsession.add(data_set)
                    data_set.name = params['name']
                    data_set['columns'] = [c.strip() for c in params['column'] if c.strip()]
                dbsession.add(experiment)
                dbsession.add(data_set)
                raise HTTPFound(request.route_url('experiment.data.view', eid=experiment.id, did=data_set.id))
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'data_set': data_set,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Data Sets',
                                    'url': request.route_url('experiment.data', eid=experiment.id)},
                                   {'title': data_set.name,
                                    'url': request.route_url('experiment.data.view',
                                                             eid=experiment.id,
                                                             did=data_set.id)},
                                   {'title': 'Edit',
                                    'url': request.route_url('experiment.data.edit',
                                                             eid=experiment.id,
                                                             did=data_set.id)}],
                        'values': request.params,
                        'errors': e.error_dict}
        return {'experiment': experiment,
                'data_set': data_set,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Data',
                            'url': request.route_url('experiment.data', eid=experiment.id)},
                           {'title': data_set.name,
                            'url': request.route_url('experiment.data.view', eid=experiment.id, did=data_set.id)},
                           {'title': 'Edit',
                            'url': request.route_url('experiment.data.edit', eid=experiment.id, did=data_set.id)}]}
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.data.item.add', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def data_item_add(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    data_set = dbsession.query(DataSet).filter(and_(DataSet.id == request.matchdict['did'],
                                                    DataSet.experiment_id == request.matchdict['eid'],
                                                    DataSet.type == 'dataset')).first()
    if experiment and data_set:
        try:
            schema = DynamicSchema()
            schema.add_field('csrf_token', CSRFValidator())
            for column in data_set['columns']:
                schema.add_field(column, formencode.validators.UnicodeString(if_empty='', if_missing=''))
            params = schema.to_python(request.params, State(request=request))
            with transaction.manager:
                dbsession.add(data_set)
                order = dbsession.query(func.max(DataItem.order)).filter(DataItem.dataset_id == data_set.id).first()
                if order[0] is None:
                    order = 1
                else:
                    order = order[0] + 1
                data_item = DataItem(dataset_id=data_set.id,
                                     order=order)
                data = {}
                for column in data_set['columns']:
                    data[column] = params[column]
                data_item['values'] = data
                dbsession.add(data_item)
            dbsession.add(data_item)
            return {'status': 'ok',
                    'id': data_item.id,
                    'order': data_item.order,
                    'values': data_item['values']}
        except formencode.Invalid as e:
            return {'status': 'error',
                    'errors': e.unpack_errors()}
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.data.item.edit', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def data_item_edit(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    data_set = dbsession.query(DataSet).filter(and_(DataSet.id == request.matchdict['did'],
                                                    DataSet.experiment_id == request.matchdict['eid'],
                                                    DataSet.type == 'dataset')).first()
    data_item = dbsession.query(DataItem).filter(and_(DataItem.id == request.matchdict['diid'],
                                                      DataItem.dataset_id == request.matchdict['did'])).first()
    if experiment and data_set and data_item:
        try:
            schema = DynamicSchema()
            schema.add_field('csrf_token', CSRFValidator())
            for column in data_set['columns']:
                schema.add_field(column, formencode.validators.UnicodeString(if_empty='', if_missing=''))
            params = schema.to_python(request.params, State(request=request))
            with transaction.manager:
                dbsession.add(data_item)
                dbsession.add(data_set)
                data = {}
                for column in data_set['columns']:
                    data[column] = params[column]
                data_item['values'] = data
            dbsession.add(data_item)
            return {'status': 'ok',
                    'id': data_item.id,
                    'order': data_item.order,
                    'values': data_item['values']}
        except formencode.Invalid as e:
            return {'status': 'error',
                    'errors': e.unpack_errors()}
        dbsession.add(experiment)
        dbsession.add(data_set)
        dbsession.add(data_item)
        raise HTTPFound(request.route_url('experiment.data.view', eid=experiment.id, did=data_set.id))
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.data.item.delete', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def data_item_delete(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    data_set = dbsession.query(DataSet).filter(and_(DataSet.id == request.matchdict['did'],
                                                    DataSet.experiment_id == request.matchdict['eid'],
                                                    DataSet.type == 'dataset')).first()
    data_item = dbsession.query(DataItem).filter(and_(DataItem.id == request.matchdict['diid'],
                                                      DataItem.dataset_id == request.matchdict['did'])).first()
    if experiment and data_set and data_item:
        with transaction.manager:
            dbsession.delete(data_item)
        dbsession.add(experiment)
        dbsession.add(data_set)
        raise HTTPFound(request.route_url('experiment.data.view', eid=experiment.id, did=data_set.id))
    else:
        raise HTTPNotFound()


class ReorderSchema(CSRFSchema):

    item = formencode.foreach.ForEach(formencode.validators.Int, convert_to_list=True)


@view_config(route_name='experiment.data.item.reorder', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def data_reorder(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    data_set = dbsession.query(DataSet).filter(and_(DataSet.id == request.matchdict['did'],
                                                    DataSet.experiment_id == request.matchdict['eid'],
                                                    DataSet.type == 'dataset')).first()
    if experiment and data_set:
        try:
            params = ReorderSchema().to_python(request.params, State(request=request))
            with transaction.manager:
                for idx, qid in enumerate(params['item']):
                    item = dbsession.query(DataItem).filter(and_(DataItem.id == qid,
                                                                 DataItem.dataset_id == data_set.id)).first()
                    if item is not None:
                        item.order = idx
            return {'status': 'ok'}
        except formencode.Invalid:
            return {'status': 'error'}
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.data.delete')
@view_config(route_name='experiment.latinsquare.delete')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
@require_method('POST')
def data_delete(request):
    mode = 'latinsquare' if 'latinsquare' in request.matched_route.name else 'dataset'
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    data_set = dbsession.query(DataSet).filter(and_(DataSet.id == request.matchdict['did'],
                                                    DataSet.experiment_id == request.matchdict['eid'],
                                                    DataSet.type == mode)).first()
    if experiment and data_set:
        try:
            CSRFSchema().to_python(request.params, State(request=request))
            with transaction.manager:
                dbsession.delete(data_set)
            dbsession.add(experiment)
            raise HTTPFound(request.route_url('experiment.%s' % mode, eid=experiment.id))
        except formencode.Invalid:
            raise HTTPFound(request.route_url('experiment.%s.view' % mode, eid=experiment.id, did=data_set.id))
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.latinsquare', renderer='ess:templates/data/latinsquare_list.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='view')
def latinsquare_list(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Latin Squares',
                            'url': request.route_url('experiment.latinsquare', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.latinsquare.create', renderer='ess:templates/data/latinsquare_create.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def latinsquare_create(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    if experiment:
        if request.method == 'POST':
            try:
                params = DataSetCreateSchema().to_python(request.params, State(request=request,
                                                                               dbsession=dbsession,
                                                                               experiment=experiment))
                with transaction.manager:
                    dbsession.add(experiment)
                    data_set = DataSet(name=params['name'],
                                       experiment=experiment,
                                       type='latinsquare')
                    data_set['columns'] = []
                    data_set['combinations'] = []
                    dbsession.add(data_set)
                dbsession.add(experiment)
                dbsession.add(data_set)
                raise HTTPFound(request.route_url('experiment.latinsquare.edit', eid=experiment.id, did=data_set.id))
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Latin Squares',
                                    'url': request.route_url('experiment.latinsquare', eid=experiment.id)},
                                   {'title': 'Add',
                                    'url': request.route_url('experiment.latinsquare.create', eid=experiment.id)}],
                        'values': request.params,
                        'errors': e.error_dict}
        return {'experiment': experiment,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Latin Squares',
                            'url': request.route_url('experiment.latinsquare', eid=experiment.id)},
                           {'title': 'Add',
                            'url': request.route_url('experiment.latinsquare.create', eid=experiment.id)}]}
    else:
        raise HTTPNotFound()


@view_config(route_name='experiment.latinsquare.view', renderer='ess:templates/data/latinsquare_view.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def latinsquare_view(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    data_set = dbsession.query(DataSet).filter(and_(DataSet.id == request.matchdict['did'],
                                                    DataSet.experiment_id == request.matchdict['eid'],
                                                    DataSet.type == 'latinsquare')).first()
    if experiment and data_set:
        source_a = dbsession.query(DataSet).filter(and_(DataSet.id == data_set['source_a'],
                                                        DataSet.type == 'dataset')).first()
        source_b = dbsession.query(DataSet).filter(and_(DataSet.id == data_set['source_b'],
                                                        DataSet.type == 'dataset')).first()
        return {'experiment': experiment,
                'data_set': data_set,
                'sources': {'a': source_a, 'b': source_b},
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Latin Squares',
                            'url': request.route_url('experiment.latinsquare', eid=experiment.id)},
                           {'title': data_set.name,
                            'url': request.route_url('experiment.data.view', eid=experiment.id, did=data_set.id)}]}
    else:
        raise HTTPNotFound()


class LatinSquareEditSchema(CSRFSchema):

    name = DataSetUniqueValidator(not_empty=True)
    source_a = DataSetExistsValidator(not_empty=True)
    mode_a = formencode.validators.OneOf(['within', 'between'])
    source_b = DataSetExistsValidator(not_empty=True)
    mode_b = formencode.validators.OneOf(['within', 'between'])


@view_config(route_name='experiment.latinsquare.edit', renderer='ess:templates/data/latinsquare_edit.kajiki')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def latinsquare_edit(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    data_set = dbsession.query(DataSet).filter(and_(DataSet.id == request.matchdict['did'],
                                                    DataSet.experiment_id == request.matchdict['eid'],
                                                    DataSet.type == 'latinsquare')).first()
    if experiment and data_set:
        if request.method == 'POST':
            try:
                params = LatinSquareEditSchema().to_python(request.params,
                                                           State(request=request,
                                                                 dbsession=dbsession,
                                                                 experiment=experiment,
                                                                 data_set=data_set))
                count = latinsquare_estimate_count(dbsession,
                                                   params['source_a'],
                                                   params['mode_a'],
                                                   params['source_b'],
                                                   params['mode_b'])
                if count > 10000:
                    raise formencode.Invalid('',
                                             None,
                                             None,
                                             error_dict={'source_a': 'These settings generate too many combinations (%s).' % count,  # noqa: E501
                                                         'source_b': 'These settings generate too many combinations (%s).' % count})  # noqa: E501
                with transaction.manager:
                    dbsession.add(data_set)
                    source_a = dbsession.query(DataSet).filter(and_(DataSet.id == params['source_a'],
                                                                    DataSet.type == 'dataset')).first()
                    source_b = dbsession.query(DataSet).filter(and_(DataSet.id == params['source_b'],
                                                                    DataSet.type == 'dataset')).first()
                    data_set.name = params['name']
                    data_set['source_a'] = int(params['source_a'])
                    data_set['mode_a'] = params['mode_a']
                    data_set['source_b'] = int(params['source_b'])
                    data_set['mode_b'] = params['mode_b']
                    data_set['columns'] = source_a['columns'] + source_b['columns']
                    data_set.items.clear()
                    combinations = []
                    if params['mode_a'] == 'within' and params['mode_b'] == 'within':
                        iterator = itertools.permutations(itertools.product(source_a.items, source_b.items))
                    elif params['mode_a'] == 'between' and params['mode_b'] == 'within':
                        iterator = []
                        for item_a in source_a.items:
                            iterator.extend(itertools.permutations(itertools.product([item_a], source_b.items)))
                    elif params['mode_a'] == 'within' and params['mode_b'] == 'between':
                        iterator = []
                        for item_b in source_b.items:
                            iterator.extend(itertools.permutations(itertools.product(source_a.items, [item_b])))
                    elif params['mode_a'] == 'between' and params['mode_b'] == 'between':
                        iterator = [[p] for p in itertools.product(source_a.items, source_b.items)]
                    order = 0
                    for data in iterator:
                        comb = []
                        for pair in data:
                            item = DataItem(data_set=data_set,
                                            order=order)
                            values = {}
                            values.update(pair[0]['values'])
                            values.update(pair[1]['values'])
                            item['values'] = values
                            comb.append(item)
                            order = order + 1
                        combinations.append(comb)
                    dbsession.flush()
                    data_set['combinations'] = [[di.id for di in c] for c in combinations]
                dbsession.add(experiment)
                dbsession.add(data_set)
                raise HTTPFound(request.route_url('experiment.latinsquare.view', eid=experiment.id, did=data_set.id))
            except formencode.Invalid as e:
                return {'experiment': experiment,
                        'data_set': data_set,
                        'crumbs': [{'title': 'Experiments',
                                    'url': request.route_url('dashboard')},
                                   {'title': experiment.title,
                                    'url': request.route_url('experiment.view', eid=experiment.id)},
                                   {'title': 'Latin Squares',
                                    'url': request.route_url('experiment.latinsquare', eid=experiment.id)},
                                   {'title': data_set.name,
                                    'url': request.route_url('experiment.latinsquare.view',
                                                             eid=experiment.id,
                                                             did=data_set.id)},
                                   {'title': 'Edit',
                                    'url': request.route_url('experiment.latinsquare.edit',
                                                             eid=experiment.id,
                                                             did=data_set.id)}],
                        'values': request.params,
                        'errors': e.error_dict}
        return {'experiment': experiment,
                'data_set': data_set,
                'crumbs': [{'title': 'Experiments',
                            'url': request.route_url('dashboard')},
                           {'title': experiment.title,
                            'url': request.route_url('experiment.view', eid=experiment.id)},
                           {'title': 'Latin Squares',
                            'url': request.route_url('experiment.latinsquare', eid=experiment.id)},
                           {'title': data_set.name,
                            'url': request.route_url('experiment.latinsquare.view',
                                                     eid=experiment.id,
                                                     did=data_set.id)},
                           {'title': 'Edit',
                            'url': request.route_url('experiment.latinsquare.edit',
                                                     eid=experiment.id,
                                                     did=data_set.id)}]}
    else:
        raise HTTPNotFound()


class LatinSquareEstimateSchema(CSRFSchema):

    source_a = DataSetExistsValidator(not_empty=True)
    mode_a = formencode.validators.OneOf(['within', 'between'])
    source_b = DataSetExistsValidator(not_empty=True)
    mode_b = formencode.validators.OneOf(['within', 'between'])


@view_config(route_name='experiment.latinsquare.edit.estimate', renderer='json')
@current_user()
@require_permission(class_=Experiment, request_key='eid', action='edit')
def latinsquare_estimate(request):
    dbsession = DBSession()
    experiment = dbsession.query(Experiment).filter(Experiment.id == request.matchdict['eid']).first()
    data_set = dbsession.query(DataSet).filter(and_(DataSet.id == request.matchdict['did'],
                                                    DataSet.experiment_id == request.matchdict['eid'],
                                                    DataSet.type == 'latinsquare')).first()
    if experiment and data_set:
        try:
            params = LatinSquareEstimateSchema().to_python(request.params,
                                                           State(request=request,
                                                                 dbsession=dbsession,
                                                                 experiment=experiment))
            count = latinsquare_estimate_count(dbsession,
                                               params['source_a'],
                                               params['mode_a'],
                                               params['source_b'],
                                               params['mode_b'])
            if count is None:
                return {'count': ''}
            else:
                return {'count': count}
        except formencode.Invalid:
            return {'count': ''}
    else:
        raise HTTPNotFound()


def latinsquare_estimate_count(dbsession, source_a, mode_a, source_b, mode_b):
        source_a = dbsession.query(DataSet).filter(and_(DataSet.id == source_a,
                                                        DataSet.type == 'dataset')).first()
        source_b = dbsession.query(DataSet).filter(and_(DataSet.id == source_b,
                                                        DataSet.type == 'dataset')).first()
        if source_a is None or source_b is None:
            return None
        count_a = dbsession.query(func.count(DataItem.id)).filter(DataItem.dataset_id == source_a.id).first()
        count_b = dbsession.query(func.count(DataItem.id)).filter(DataItem.dataset_id == source_b.id).first()
        if mode_a == 'within' and mode_b == 'within':
            return factorial(count_a[0] * count_b[0])
        elif mode_a == 'between' and mode_b == 'within':
            return count_a[0] * factorial(count_b[0])
        elif mode_a == 'within' and mode_b == 'between':
            return factorial(count_a[0]) * count_b[0]
        elif mode_a == 'between' and mode_b == 'between':
            return count_a[0] * count_b[0]
