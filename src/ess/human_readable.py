def experiment_status(status):
    if status == 'develop':
        return 'In Development'
    elif status == 'live':
        return 'Live'
    elif status == 'paused':
        return 'Paused'
    elif status == 'completed':
        return 'Completed'
    else:
        return ''


def question_error(question, data_item, errors, sub_question=None):
    if question['frontend', 'display_as'] != 'text':
        did = 'd%s' % data_item.id
        if did in errors:
            if isinstance(errors[did], str):
                return errors[did]
            qname = question['name']
            if qname in errors[did]:
                if isinstance(errors[did][qname], str):
                    return errors[did][qname]
                if sub_question:
                    if sub_question in errors[did][qname]:
                        return errors[did][qname][sub_question]
                else:
                    return '. '.join(set(errors[did][qname].values()))
    return None
