from ess.models import QuestionTypeGroup, QuestionType


def load_question_types(dbsession, data):
    qtgroups = {}
    qtypes = {}
    for obj in data['data']:
        if obj['type'] == 'question_type_groups':
            qtgroups[obj['id']] = QuestionTypeGroup(name=obj['id'],
                                                    title=obj['attributes']['title'],
                                                    order=obj['attributes']['order']
                                                    if 'order' in obj['attributes'] else 0)
            dbsession.add(qtgroups[obj['id']])
        elif obj['type'] == 'question_type':
            qtypes[obj['id']] = QuestionType(name=obj['id'],
                                             title=obj['attributes']['title'],
                                             order=obj['attributes']['order']
                                             if 'order' in obj['attributes'] else 0,
                                             backend=obj['attributes']['backend'] if
                                             'backend' in obj['attributes'] else {},
                                             frontend=obj['attributes']['frontend'] if
                                             'frontend' in obj['attributes'] else {})
            dbsession.add(qtypes[obj['id']])
    for obj in data['data']:
        if obj['type'] == 'question_type_groups':
            if 'relationships' in obj and 'parent' in obj['relationships']:
                if obj['relationships']['parent']['data']['id'] in qtgroups:
                    qtgroups[obj['id']].parent = qtgroups[obj['relationships']['parent']['data']['id']]
        elif obj['type'] == 'question_type':
            if 'relationships' in obj and 'q_type_group' in obj['relationships']:
                if obj['relationships']['q_type_group']['data']['id'] in qtgroups:
                    qtypes[obj['id']].q_type_group = qtgroups[obj['relationships']['q_type_group']['data']['id']]
