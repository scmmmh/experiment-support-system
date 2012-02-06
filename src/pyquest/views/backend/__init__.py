# -*- coding: utf-8 -*-

def init(config):
    config.add_route('survey.overview', '/surveys/{sid}')
    config.add_route('survey.data', '/surveys/{sid}/data')
    config.add_route('survey.data.upload', '/surveys/{sid}/data/upload')
    config.add_route('survey.data.new', '/surveys/{sid}/data/new')
    config.add_route('survey.data.edit', '/surveys/{sid}/data/{did}/edit')
    config.add_route('survey.data.delete', '/surveys/{sid}/data/{did}/delete')
    config.add_route('survey.data.clear', '/surveys/{sid}/data/clear')
    config.add_route('survey.new', '/surveys/new')
    config.add_route('survey.edit', '/surveys/{sid}/edit')
    config.add_route('survey.qsheet', '/surveys/{sid}/qsheets')
    config.add_route('survey.qsheet.order', '/surveys/{sid}/qsheets/order')
    config.add_route('survey.qsheet.new', '/surveys/{sid}/qsheets/new')
    config.add_route('survey.qsheet.edit', '/surveys/{sid}/qsheets/{qsid}/edit')
    config.add_route('survey.qsheet.delete', '/surveys/{sid}/qsheets/{qsid}/delete')
    config.add_route('survey.qsheet.preview', '/surveys/{sid}/preview/{qsid}')
    config.add_route('survey.preview', '/surveys/{sid}/preview')
