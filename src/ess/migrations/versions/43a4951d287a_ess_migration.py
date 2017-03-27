"""
################################################
Migrate the pyquest schema to the new ess schema
################################################

This is a destructive one-way migration.

Revision ID: 43a4951d287a
Revises: 7f8cc2026730
Create Date: 2017-03-17 09:09:51.279492
"""
import json
import sqlalchemy as sa

from alembic import op
from datetime import datetime, timedelta

# revision identifiers, used by Alembic.
revision = '43a4951d287a'
down_revision = '7f8cc2026730'

metadata = sa.MetaData()
transitions = sa.Table('transitions', metadata,
                       sa.Column('id', sa.Integer(), primary_key=True),
                       sa.Column('source_id', sa.Integer()),
                       sa.Column('target_id', sa.Integer()),
                       sa.Column('_condition', sa.UnicodeText()),
                       sa.Column('_action', sa.UnicodeText()),
                       sa.Column('attributes', sa.UnicodeText()),
                       sa.Column('order', sa.Integer()))
pages = sa.Table('pages', metadata,
                 sa.Column('id', sa.Integer(), primary_key=True),
                 sa.Column('dataset_id', sa.Integer()),
                 sa.Column('attributes', sa.UnicodeText()),
                 sa.Column('name', sa.Unicode(255)),
                 sa.Column('experiment_id', sa.Integer()))
qsheet_attributes = sa.Table('qsheet_attributes', metadata,
                             sa.Column('id', sa.Integer(), primary_key=True),
                             sa.Column('qsheet_id', sa.Integer()),
                             sa.Column('key', sa.Unicode()),
                             sa.Column('value', sa.UnicodeText()))
data_sets = sa.Table('data_sets', metadata,
                     sa.Column('id', sa.Integer(), primary_key=True),
                     sa.Column('type', sa.Unicode(255)),
                     sa.Column('attributes', sa.UnicodeText()))
questions = sa.Table('questions', metadata,
                     sa.Column('id', sa.Integer(), primary_key=True),
                     sa.Column('page_id', sa.Integer()),
                     sa.Column('name', sa.Unicode(255)),
                     sa.Column('title', sa.Unicode(255)),
                     sa.Column('required', sa.Boolean()),
                     sa.Column('help', sa.UnicodeText()),
                     sa.Column('attributes', sa.UnicodeText()),
                     sa.Column('type_id', sa.Integer()))
question_complex_attributes = sa.Table('question_complex_attributes', metadata,
                                       sa.Column('id', sa.Integer(), primary_key=True),
                                       sa.Column('question_id', sa.Integer()),
                                       sa.Column('key', sa.Unicode(255)),
                                       sa.Column('order', sa.Integer()))
question_attributes = sa.Table('question_attributes', metadata,
                               sa.Column('id', sa.Integer(), primary_key=True),
                               sa.Column('question_group_id', sa.Integer()),
                               sa.Column('key', sa.Unicode(255)),
                               sa.Column('value', sa.UnicodeText()),
                               sa.Column('order', sa.Integer()))
question_type_groups = sa.Table('question_type_groups', metadata,
                                sa.Column('id', sa.Integer(), primary_key=True),
                                sa.Column('name', sa.Unicode(255)),
                                sa.Column('title', sa.Unicode(255)),
                                sa.Column('order', sa.Integer()),
                                sa.Column('parent_id', sa.Integer()),
                                sa.Column('enabled', sa.Boolean()))
question_types = sa.Table('question_types', metadata,
                          sa.Column('id', sa.Integer(), primary_key=True),
                          sa.Column('name', sa.Unicode(255)),
                          sa.Column('title', sa.Unicode(255)),
                          sa.Column('frontend', sa.UnicodeText()),
                          sa.Column('backend', sa.UnicodeText()),
                          sa.Column('group_id', sa.Integer()),
                          sa.Column('parent_id', sa.Integer()),
                          sa.Column('enabled', sa.Boolean()),
                          sa.Column('order', sa.Integer()))

data_set_attribute_keys = sa.Table('data_set_attribute_keys', metadata,
                                   sa.Column('id', sa.Integer(), primary_key=True),
                                   sa.Column('dataset_id', sa.Integer()),
                                   sa.Column('key', sa.Unicode(255)),
                                   sa.Column('order', sa.Integer()))
data_set_relations = sa.Table('data_set_relations', metadata,
                              sa.Column('id', sa.Integer(), primary_key=True),
                              sa.Column('subject_id', sa.Integer()),
                              sa.Column('object_id', sa.Integer()),
                              sa.Column('rel', sa.Unicode(255)),
                              sa.Column('_data', sa.UnicodeText()))
data_items = sa.Table('data_items', metadata,
                      sa.Column('id', sa.Integer(), primary_key=True),
                      sa.Column('order', sa.Integer()),
                      sa.Column('control', sa.Boolean()),
                      sa.Column('dataset_id', sa.Integer()),
                      sa.Column('attributes', sa.UnicodeText()))
data_item_attributes = sa.Table('data_item_attributes', metadata,
                                sa.Column('id', sa.Integer(), primary_key=True),
                                sa.Column('data_item_id', sa.Integer()),
                                sa.Column('key_id', sa.Integer()),
                                sa.Column('value', sa.UnicodeText()))
data_item_control_answers = sa.Table('data_item_control_answers', metadata,
                                     sa.Column('id', sa.Integer(), primary_key=True),
                                     sa.Column('data_item_id', sa.Integer()),
                                     sa.Column('question_id', sa.Integer()),
                                     sa.Column('answer', sa.UnicodeText()))
participants = sa.Table('participants', metadata,
                        sa.Column('id', sa.Integer(), primary_key=True),
                        sa.Column('experiment_id', sa.Integer()),
                        sa.Column('completed', sa.Boolean()),
                        sa.Column('started', sa.DateTime()),
                        sa.Column('updated', sa.DateTime()),
                        sa.Column('attributes', sa.UnicodeText()))
answers = sa.Table('answers', metadata,
                   sa.Column('id', sa.Integer(), primary_key=True),
                   sa.Column('participant_id', sa.Integer()),
                   sa.Column('question_id', sa.Integer()),
                   sa.Column('data_item_id', sa.Integer()),
                   sa.Column('attributes', sa.UnicodeText()))
answer_values = sa.Table('answer_values', metadata,
                         sa.Column('id', sa.Integer(), primary_key=True),
                         sa.Column('answer_id', sa.Integer()),
                         sa.Column('name', sa.Unicode(255)),
                         sa.Column('value', sa.Unicode(4096)))

NEW_QUESTION_TYPES = {'text': {'frontend': '{"text": "<p>Enter the text to display.</p>", "display_as": "text", "visible": true, "width": "small-12", "generates_response": false}',
                               'backend': '{"fields": [{"name": "text", "type": "textarea", "title": "HTML Snippet", "extra_attrs": {"style": "height: 10rem"}, "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}}]}'},
                      'simple_input': {'frontend': '{"display_as": "simple_input", "input_type": "text", "visible": true, "width": "small-12 medium-6", "generates_response": true}',
                                       'backend': '''{"fields": [{"name": "name", "type": "text", "title": "Unique Name", "validation": {"type": "unicode", "not_empty": true}},
                                           {"name": "title", "type": "text", "title": "Title", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "input_type", "type": "select", "title": "Answer Type",
                                            "values": [["text", "Single-line Free Text"], ["textarea", "Multi-line Free Text"], ["number", "Number"],
                                                       ["email", "E-Mail Address"], ["url", "URL"], ["date", "Date"], ["time", "Time"],
                                                       ["datetime", "Date & Time"], ["month", "Month"]],
                                            "validation": {"type": "oneof", "values": ["text", "textarea", "number", "email", "url", "date",
                                                                                       "time", "datetime", "month"]}},
                                           {"name": "required", "type": "checkbox", "title": "Required", "validation": {"type": "boolean", "if_empty": "", "if_missing": ""}},
                                           {"name": "help", "type": "textarea", "title": "Help", "extra_attrs": {"style": "height: 5rem"}, "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}}]}'''},
                      'select_simple_choice': {'frontend': '{"display_as": "select_simple_choice", "visible": true, "answers": [], "widget": "list", "width": "small-12", "generates_response": true}',
                                               'backend': '''{"fields": [{"name": "name", "type": "text", "title": "Unique Name", "validation": {"type": "unicode", "not_empty": true}},
                                           {"name": "title", "type": "text", "title": "Title", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "widget", "type": "select", "title": "Answer Type",
                                            "values": [["list", "List of Answers"], ["select", "Drop-down Selection"], ["table", "Table of Answers"]],
                                            "validation": {"type": "oneof", "values": ["list", "select", "table"]}},
                                           {"name": "required", "type": "checkbox", "title": "Required", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "help", "type": "textarea", "title": "Help", "extra_attrs": {"style": "height: 5rem"}, "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "answers", "type": "table", "title": "Answers",
                                            "fields": [{"name": "value", "title": "Answer", "validation": {"type": "unicode", "if_empty": null, "if_missing": null}},
                                                       {"name": "label", "title": "Label (optional)", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}}],
                                            "validation": {"type": "foreach", "sub_type": "nested"}},
                                           {"name": "allow_other", "type": "checkbox", "title": "Allow other Answers", "validation": {"type": "boolean", "if_empty": "", "if_missing": ""}},
                                           {"name": "allow_multiple", "type": "checkbox", "title": "Allow multiple Answers", "validation": {"type": "boolean", "if_empty": "", "if_missing": ""}},
                                           {"name": "before_label", "type": "text", "title": "Before Label", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "after_label", "type": "text", "title": "After Label", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}}]}'''},
                      'select_grid_choice': {'frontend': '{"display_as": "select_grid_choice", "visible": true, "answers": [], "questions": [], "generates_response": true}',
                                             'backend': '''{"fields": [{"name": "name", "type": "text", "title": "Unique Name", "validation": {"type": "unicode", "not_empty": true}},
                                           {"name": "title", "type": "text", "title": "Title", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "required", "type": "checkbox", "title": "Required", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "help", "type": "textarea", "title": "Help", "extra_attrs": {"style": "height: 5rem"}, "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "questions", "type": "table", "title": "Sub-Questions",
                                            "fields": [{"name": "name", "title": "Name", "validation": {"type": "unicode", "if_empty": null, "if_missing": null}},
                                                       {"name": "label", "title": "Title", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}}],
                                            "validation": {"type": "foreach", "sub_type": "nested"}},
                                           {"name": "answers", "type": "table", "title": "Answers",
                                            "fields": [{"name": "value", "title": "Answer", "validation": {"type": "unicode", "if_empty": null, "if_missing": null}},
                                                       {"name": "label", "title": "Label (optional)", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}}],
                                            "validation": {"type": "foreach", "sub_type": "nested"}},
                                           {"name": "allow_multiple", "type": "checkbox", "title": "Allow multiple Answers", "validation": {"type": "boolean", "if_empty": "", "if_missing": ""}},
                                           {"name": "before_label", "type": "text", "title": "Before Label", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "after_label", "type": "text", "title": "After Label", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}}]}'''},
                      'ranking': {'frontend': '''{"display_as": "ranking", "visible": true, "answers": [], "javascript": "question.find('.answer-list').sortable();question.on('click', 'a.up', function(){var item=$(this).parent().parent();item.prev('li').before(item);});question.on('click', 'a.down', function(){var item=$(this).parent().parent();item.next('li').after(item);});", "generates_response": true}''',
                                  'backend': '''{"fields": [{"name": "name", "type": "text", "title": "Unique Name", "validation": {"type": "unicode", "not_empty": true}},
                                           {"name": "title", "type": "text", "title": "Title", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "required", "type": "checkbox", "title": "Required", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "help", "type": "textarea", "title": "Help", "extra_attrs": {"style": "height: 5rem"}, "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "answers", "type": "table", "title": "Answers",
                                            "fields": [{"name": "value", "title": "Answer", "validation": {"type": "unicode", "if_empty": null, "if_missing": null}},
                                                       {"name": "label", "title": "Label (optional)", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}}],
                                            "validation": {"type": "foreach", "sub_type": "nested"}}]}'''},
                      'hidden_value': {'frontend': '{"display_as": "simple_input", "input_type": "hidden", "visible": false, "value": "", "generates_response": true}',
                                       'backend': '''{"fields": [{"name": "name", "type": "text", "title": "Unique Name", "validation": {"type": "unicode", "not_empty": true}},
                                           {"name": "value", "type": "text", "title": "Value", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}}]}'''},
                      'page_timer': {'frontend': '''{"display_as": "simple_input", "input_type": "hidden", "visible": false, "value": "", "javascript": "var form=question.parents('form');var start=Date.now();form.on('submit', function() {var input=question.find('input[type=hidden]');var end=Date.now();input.val((end-start)/1000);});", "generates_response": true}''',
                                     'backend': '''{"fields": [{"name": "name", "type": "text", "title": "Unique Name", "validation": {"type": "unicode", "not_empty": true}}]}'''},
                      'auto_submit': {'frontend': '''{"display_as": "simple_input", "input_type": "hidden", "visible": false, "value": "", "javascript": "var form=question.parents('form');setTimeout(function() {form.find('button[data-action=next-page]').trigger('click');}, parseInt(${delay})*1000);", "generates_response": false}''',
                                      'backend': '''{"fields": [{"name": "name", "type": "text", "title": "Unique Name", "validation": {"type": "unicode", "not_empty": true}},
                                           {"name": "delay", "type": "text", "title": "Delay (seconds)", "validation": {"type": "number", "not_empty": true}}]}'''},
                      'country': {'frontend': '''{"answers": [{"label": "Afghanistan", "value": "AF"}, {"label": "Africa", "value": "002"}, {"label": "Albania", "value": "AL"}, {"label": "Algeria", "value": "DZ"}, {"label": "American Samoa", "value": "AS"}, {"label": "Americas", "value": "019"}, {"label": "Andorra", "value": "AD"}, {"label": "Angola", "value": "AO"}, {"label": "Anguilla", "value": "AI"}, {"label": "Antarctica", "value": "AQ"}, 
                                             {"label": "Antigua & Barbuda", "value": "AG"}, {"label": "Argentina", "value": "AR"}, {"label": "Armenia", "value": "AM"}, {"label": "Aruba", "value": "AW"}, {"label": "Ascension Island", "value": "AC"}, {"label": "Asia", "value": "142"}, {"label": "Australasia", "value": "053"}, {"label": "Australia", "value": "AU"}, {"label": "Austria", "value": "AT"}, {"label": "Azerbaijan", "value": "AZ"}, 
                                             {"label": "Bahamas", "value": "BS"}, {"label": "Bahrain", "value": "BH"}, {"label": "Bangladesh", "value": "BD"}, {"label": "Barbados", "value": "BB"}, {"label": "Belarus", "value": "BY"}, {"label": "Belgium", "value": "BE"}, {"label": "Belize", "value": "BZ"}, {"label": "Benin", "value": "BJ"}, {"label": "Bermuda", "value": "BM"}, {"label": "Bhutan", "value": "BT"}, 
                                             {"label": "Bolivia", "value": "BO"}, {"label": "Bosnia & Herzegovina", "value": "BA"}, {"label": "Botswana", "value": "BW"}, {"label": "Bouvet Island", "value": "BV"}, {"label": "Brazil", "value": "BR"}, {"label": "British Indian Ocean Territory", "value": "IO"}, {"label": "British Virgin Islands", "value": "VG"}, {"label": "Brunei", "value": "BN"}, {"label": "Bulgaria", "value": "BG"}, {"label": "Burkina Faso", "value": "BF"}, 
                                             {"label": "Burundi", "value": "BI"}, {"label": "Cambodia", "value": "KH"}, {"label": "Cameroon", "value": "CM"}, {"label": "Canada", "value": "CA"}, {"label": "Canary Islands", "value": "IC"}, {"label": "Cape Verde", "value": "CV"}, {"label": "Caribbean", "value": "029"}, {"label": "Caribbean Netherlands", "value": "BQ"}, {"label": "Cayman Islands", "value": "KY"}, {"label": "Central African Republic", "value": "CF"}, 
                                             {"label": "Central America", "value": "013"}, {"label": "Central Asia", "value": "143"}, {"label": "Ceuta & Melilla", "value": "EA"}, {"label": "Chad", "value": "TD"}, {"label": "Chile", "value": "CL"}, {"label": "China", "value": "CN"}, {"label": "Christmas Island", "value": "CX"}, {"label": "Clipperton Island", "value": "CP"}, {"label": "Cocos (Keeling) Islands", "value": "CC"}, {"label": "Colombia", "value": "CO"}, 
                                             {"label": "Comoros", "value": "KM"}, {"label": "Congo - Brazzaville", "value": "CG"}, {"label": "Congo - Kinshasa", "value": "CD"}, {"label": "Cook Islands", "value": "CK"}, {"label": "Costa Rica", "value": "CR"}, {"label": "Croatia", "value": "HR"}, {"label": "Cuba", "value": "CU"}, {"label": "Cura\u00e7ao", "value": "CW"}, {"label": "Cyprus", "value": "CY"}, {"label": "Czech Republic", "value": "CZ"}, 
                                             {"label": "C\u00f4te d\u2019Ivoire", "value": "CI"}, {"label": "Denmark", "value": "DK"}, {"label": "Diego Garcia", "value": "DG"}, {"label": "Djibouti", "value": "DJ"}, {"label": "Dominica", "value": "DM"}, {"label": "Dominican Republic", "value": "DO"}, {"label": "Eastern Africa", "value": "014"}, {"label": "Eastern Asia", "value": "030"}, {"label": "Eastern Europe", "value": "151"}, {"label": "Ecuador", "value": "EC"}, 
                                             {"label": "Egypt", "value": "EG"}, {"label": "El Salvador", "value": "SV"}, {"label": "Equatorial Guinea", "value": "GQ"}, {"label": "Eritrea", "value": "ER"}, {"label": "Estonia", "value": "EE"}, {"label": "Ethiopia", "value": "ET"}, {"label": "Europe", "value": "150"}, {"label": "European Union", "value": "EU"}, {"label": "Falkland Islands", "value": "FK"}, {"label": "Faroe Islands", "value": "FO"}, 
                                             {"label": "Fiji", "value": "FJ"}, {"label": "Finland", "value": "FI"}, {"label": "France", "value": "FR"}, {"label": "French Guiana", "value": "GF"}, {"label": "French Polynesia", "value": "PF"}, {"label": "French Southern Territories", "value": "TF"}, {"label": "Gabon", "value": "GA"}, {"label": "Gambia", "value": "GM"}, {"label": "Georgia", "value": "GE"}, {"label": "Germany", "value": "DE"}, 
                                             {"label": "Ghana", "value": "GH"}, {"label": "Gibraltar", "value": "GI"}, {"label": "Greece", "value": "GR"}, {"label": "Greenland", "value": "GL"}, {"label": "Grenada", "value": "GD"}, {"label": "Guadeloupe", "value": "GP"}, {"label": "Guam", "value": "GU"}, {"label": "Guatemala", "value": "GT"}, {"label": "Guernsey", "value": "GG"}, {"label": "Guinea", "value": "GN"}, 
                                             {"label": "Guinea-Bissau", "value": "GW"}, {"label": "Guyana", "value": "GY"}, {"label": "Haiti", "value": "HT"}, {"label": "Heard & McDonald Islands", "value": "HM"}, {"label": "Honduras", "value": "HN"}, {"label": "Hong Kong SAR China", "value": "HK"}, {"label": "Hungary", "value": "HU"}, {"label": "Iceland", "value": "IS"}, {"label": "India", "value": "IN"}, {"label": "Indonesia", "value": "ID"}, 
                                             {"label": "Iran", "value": "IR"}, {"label": "Iraq", "value": "IQ"}, {"label": "Ireland", "value": "IE"}, {"label": "Isle of Man", "value": "IM"}, {"label": "Israel", "value": "IL"}, {"label": "Italy", "value": "IT"}, {"label": "Jamaica", "value": "JM"}, {"label": "Japan", "value": "JP"}, {"label": "Jersey", "value": "JE"}, {"label": "Jordan", "value": "JO"}, 
                                             {"label": "Kazakhstan", "value": "KZ"}, {"label": "Kenya", "value": "KE"}, {"label": "Kiribati", "value": "KI"}, {"label": "Kosovo", "value": "XK"}, {"label": "Kuwait", "value": "KW"}, {"label": "Kyrgyzstan", "value": "KG"}, {"label": "Laos", "value": "LA"}, {"label": "Latin America", "value": "419"}, {"label": "Latvia", "value": "LV"}, {"label": "Lebanon", "value": "LB"}, 
                                             {"label": "Lesotho", "value": "LS"}, {"label": "Liberia", "value": "LR"}, {"label": "Libya", "value": "LY"}, {"label": "Liechtenstein", "value": "LI"}, {"label": "Lithuania", "value": "LT"}, {"label": "Luxembourg", "value": "LU"}, {"label": "Macau SAR China", "value": "MO"}, {"label": "Macedonia", "value": "MK"}, {"label": "Madagascar", "value": "MG"}, {"label": "Malawi", "value": "MW"}, 
                                             {"label": "Malaysia", "value": "MY"}, {"label": "Maldives", "value": "MV"}, {"label": "Mali", "value": "ML"}, {"label": "Malta", "value": "MT"}, {"label": "Marshall Islands", "value": "MH"}, {"label": "Martinique", "value": "MQ"}, {"label": "Mauritania", "value": "MR"}, {"label": "Mauritius", "value": "MU"}, {"label": "Mayotte", "value": "YT"}, {"label": "Melanesia", "value": "054"}, 
                                             {"label": "Mexico", "value": "MX"}, {"label": "Micronesia", "value": "FM"}, {"label": "Micronesian Region", "value": "057"}, {"label": "Middle Africa", "value": "017"}, {"label": "Moldova", "value": "MD"}, {"label": "Monaco", "value": "MC"}, {"label": "Mongolia", "value": "MN"}, {"label": "Montenegro", "value": "ME"}, {"label": "Montserrat", "value": "MS"}, {"label": "Morocco", "value": "MA"}, 
                                             {"label": "Mozambique", "value": "MZ"}, {"label": "Myanmar (Burma)", "value": "MM"}, {"label": "Namibia", "value": "NA"}, {"label": "Nauru", "value": "NR"}, {"label": "Nepal", "value": "NP"}, {"label": "Netherlands", "value": "NL"}, {"label": "Netherlands Antilles", "value": "AN"}, {"label": "New Caledonia", "value": "NC"}, {"label": "New Zealand", "value": "NZ"}, {"label": "Nicaragua", "value": "NI"}, 
                                             {"label": "Niger", "value": "NE"}, {"label": "Nigeria", "value": "NG"}, {"label": "Niue", "value": "NU"}, {"label": "Norfolk Island", "value": "NF"}, {"label": "North America", "value": "003"}, {"label": "North Korea", "value": "KP"}, {"label": "Northern Africa", "value": "015"}, {"label": "Northern America", "value": "021"}, {"label": "Northern Europe", "value": "154"}, {"label": "Northern Mariana Islands", "value": "MP"}, 
                                             {"label": "Norway", "value": "NO"}, {"label": "Oceania", "value": "009"}, {"label": "Oman", "value": "OM"}, {"label": "Outlying Oceania", "value": "QO"}, {"label": "Pakistan", "value": "PK"}, {"label": "Palau", "value": "PW"}, {"label": "Palestinian Territories", "value": "PS"}, {"label": "Panama", "value": "PA"}, {"label": "Papua New Guinea", "value": "PG"}, {"label": "Paraguay", "value": "PY"}, 
                                             {"label": "Peru", "value": "PE"}, {"label": "Philippines", "value": "PH"}, {"label": "Pitcairn Islands", "value": "PN"}, {"label": "Poland", "value": "PL"}, {"label": "Polynesia", "value": "061"}, {"label": "Portugal", "value": "PT"}, {"label": "Puerto Rico", "value": "PR"}, {"label": "Qatar", "value": "QA"}, {"label": "Romania", "value": "RO"}, {"label": "Russia", "value": "RU"}, 
                                             {"label": "Rwanda", "value": "RW"}, {"label": "R\u00e9union", "value": "RE"}, {"label": "Samoa", "value": "WS"}, {"label": "San Marino", "value": "SM"}, {"label": "Saudi Arabia", "value": "SA"}, {"label": "Senegal", "value": "SN"}, {"label": "Serbia", "value": "RS"}, {"label": "Seychelles", "value": "SC"}, {"label": "Sierra Leone", "value": "SL"}, {"label": "Singapore", "value": "SG"}, 
                                             {"label": "Sint Maarten", "value": "SX"}, {"label": "Slovakia", "value": "SK"}, {"label": "Slovenia", "value": "SI"}, {"label": "Solomon Islands", "value": "SB"}, {"label": "Somalia", "value": "SO"}, {"label": "South Africa", "value": "ZA"}, {"label": "South America", "value": "005"}, {"label": "South Georgia & South Sandwich Islands", "value": "GS"}, {"label": "South Korea", "value": "KR"}, {"label": "South Sudan", "value": "SS"}, 
                                             {"label": "Southeast Asia", "value": "035"}, {"label": "Southern Africa", "value": "018"}, {"label": "Southern Asia", "value": "034"}, {"label": "Southern Europe", "value": "039"}, {"label": "Spain", "value": "ES"}, {"label": "Sri Lanka", "value": "LK"}, {"label": "St. Barth\u00e9lemy", "value": "BL"}, {"label": "St. Helena", "value": "SH"}, {"label": "St. Kitts & Nevis", "value": "KN"}, {"label": "St. Lucia", "value": "LC"}, 
                                             {"label": "St. Martin", "value": "MF"}, {"label": "St. Pierre & Miquelon", "value": "PM"}, {"label": "St. Vincent & Grenadines", "value": "VC"}, {"label": "Sudan", "value": "SD"}, {"label": "Suriname", "value": "SR"}, {"label": "Svalbard & Jan Mayen", "value": "SJ"}, {"label": "Swaziland", "value": "SZ"}, {"label": "Sweden", "value": "SE"}, {"label": "Switzerland", "value": "CH"}, {"label": "Syria", "value": "SY"}, 
                                             {"label": "S\u00e3o Tom\u00e9 & Pr\u00edncipe", "value": "ST"}, {"label": "Taiwan", "value": "TW"}, {"label": "Tajikistan", "value": "TJ"}, {"label": "Tanzania", "value": "TZ"}, {"label": "Thailand", "value": "TH"}, {"label": "Timor-Leste", "value": "TL"}, {"label": "Togo", "value": "TG"}, {"label": "Tokelau", "value": "TK"}, {"label": "Tonga", "value": "TO"}, {"label": "Trinidad & Tobago", "value": "TT"}, 
                                             {"label": "Tristan da Cunha", "value": "TA"}, {"label": "Tunisia", "value": "TN"}, {"label": "Turkey", "value": "TR"}, {"label": "Turkmenistan", "value": "TM"}, {"label": "Turks & Caicos Islands", "value": "TC"}, {"label": "Tuvalu", "value": "TV"}, {"label": "U.S. Outlying Islands", "value": "UM"}, {"label": "U.S. Virgin Islands", "value": "VI"}, {"label": "Uganda", "value": "UG"}, {"label": "Ukraine", "value": "UA"}, 
                                             {"label": "United Arab Emirates", "value": "AE"}, {"label": "United Kingdom", "value": "GB"}, {"label": "United States", "value": "US"}, {"label": "Unknown Region", "value": "ZZ"}, {"label": "Uruguay", "value": "UY"}, {"label": "Uzbekistan", "value": "UZ"}, {"label": "Vanuatu", "value": "VU"}, {"label": "Vatican City", "value": "VA"}, {"label": "Venezuela", "value": "VE"}, {"label": "Vietnam", "value": "VN"}, 
                                             {"label": "Wallis & Futuna", "value": "WF"}, {"label": "Western Africa", "value": "011"}, {"label": "Western Asia", "value": "145"}, {"label": "Western Europe", "value": "155"}, {"label": "Western Sahara", "value": "EH"}, {"label": "World", "value": "001"}, {"label": "Yemen", "value": "YE"}, {"label": "Zambia", "value": "ZM"}, {"label": "Zimbabwe", "value": "ZW"}, {"label": "\u00c5land Islands", "value": "AX"}],
                                 "widget": "select", "highlight": "",
                                 "javascript": "var highlights = '${highlight}';if(highlights.trim()!=''){highlights=highlights.split(',');}if(highlights.length>0){var marker=question.find('select option:first-child()');for(var idx=0;idx<highlights.length;idx++){var elem=question.find('option[value=' + highlights[idx].trim() + ']');if(elem.length>0){marker.after(elem);marker=elem;}}marker.after('<option value=\\\\'\\\\'>------------------------------</option>');}",
                                 "generates_response": true}''',
                                  'backend': '''{"fields": [{"name": "name", "type": "text", "title": "Unique Name", "validation": {"type": "unicode", "not_empty": true}},
                                           {"name": "title", "type": "text", "title": "Title", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "required", "type": "checkbox", "title": "Required", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "help", "type": "textarea", "title": "Help", "extra_attrs": {"style": "height: 5rem"}, "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "allow_multiple", "type": "checkbox", "title": "Allow multiple Answers", "validation": {"type": "boolean", "if_empty": "", "if_missing": ""}},
                                           {"name": "highlight", "type": "text", "title": "Highlight these Countries (uppercase country codes separated by commas)", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}}
                                           ]}'''},
                      'language': {'frontend': '''{"answers": [{"label": "Abkhazian", "value": "ab"}, {"label": "Achinese", "value": "ace"}, {"label": "Acoli", "value": "ach"}, {"label": "Adangme", "value": "ada"}, {"label": "Adyghe", "value": "ady"}, {"label": "Afar", "value": "aa"}, {"label": "Afrihili", "value": "afh"}, {"label": "Afrikaans", "value": "af"}, {"label": "Aghem", "value": "agq"}, {"label": "Ainu", "value": "ain"}, 
                                             {"label": "Akan", "value": "ak"}, {"label": "Akkadian", "value": "akk"}, {"label": "Akoose", "value": "bss"}, {"label": "Alabama", "value": "akz"}, {"label": "Albanian", "value": "sq"}, {"label": "Aleut", "value": "ale"}, {"label": "Algerian Arabic", "value": "arq"}, {"label": "American Sign Language", "value": "ase"}, {"label": "Amharic", "value": "am"}, {"label": "Ancient Egyptian", "value": "egy"}, 
                                             {"label": "Ancient Greek", "value": "grc"}, {"label": "Angika", "value": "anp"}, {"label": "Ao Naga", "value": "njo"}, {"label": "Arabic", "value": "ar"}, {"label": "Aragonese", "value": "an"}, {"label": "Aramaic", "value": "arc"}, {"label": "Araona", "value": "aro"}, {"label": "Arapaho", "value": "arp"}, {"label": "Arawak", "value": "arw"}, {"label": "Armenian", "value": "hy"}, 
                                             {"label": "Aromanian", "value": "rup"}, {"label": "Arpitan", "value": "frp"}, {"label": "Assamese", "value": "as"}, {"label": "Asturian", "value": "ast"}, {"label": "Asu", "value": "asa"}, {"label": "Atsam", "value": "cch"}, {"label": "Avaric", "value": "av"}, {"label": "Avestan", "value": "ae"}, {"label": "Awadhi", "value": "awa"}, {"label": "Aymara", "value": "ay"}, 
                                             {"label": "Azerbaijani", "value": "az"}, {"label": "Badaga", "value": "bfq"}, {"label": "Bafia", "value": "ksf"}, {"label": "Bafut", "value": "bfd"}, {"label": "Bakhtiari", "value": "bqi"}, {"label": "Balinese", "value": "ban"}, {"label": "Baluchi", "value": "bal"}, {"label": "Bambara", "value": "bm"}, {"label": "Bamun", "value": "bax"}, {"label": "Banjar", "value": "bjn"}, 
                                             {"label": "Basaa", "value": "bas"}, {"label": "Bashkir", "value": "ba"}, {"label": "Basque", "value": "eu"}, {"label": "Batak Toba", "value": "bbc"}, {"label": "Bavarian", "value": "bar"}, {"label": "Beja", "value": "bej"}, {"label": "Belarusian", "value": "be"}, {"label": "Bemba", "value": "bem"}, {"label": "Bena", "value": "bez"}, {"label": "Bengali", "value": "bn"}, 
                                             {"label": "Betawi", "value": "bew"}, {"label": "Bhojpuri", "value": "bho"}, {"label": "Bikol", "value": "bik"}, {"label": "Bini", "value": "bin"}, {"label": "Bishnupriya", "value": "bpy"}, {"label": "Bislama", "value": "bi"}, {"label": "Blin", "value": "byn"}, {"label": "Blissymbols", "value": "zbl"}, {"label": "Bodo", "value": "brx"}, {"label": "Bosnian", "value": "bs"}, 
                                             {"label": "Brahui", "value": "brh"}, {"label": "Braj", "value": "bra"}, {"label": "Breton", "value": "br"}, {"label": "Buginese", "value": "bug"}, {"label": "Bulgarian", "value": "bg"}, {"label": "Bulu", "value": "bum"}, {"label": "Buriat", "value": "bua"}, {"label": "Burmese", "value": "my"}, {"label": "Caddo", "value": "cad"}, {"label": "Cajun French", "value": "frc"}, 
                                             {"label": "Cantonese", "value": "yue"}, {"label": "Capiznon", "value": "cps"}, {"label": "Carib", "value": "car"}, {"label": "Catalan", "value": "ca"}, {"label": "Cayuga", "value": "cay"}, {"label": "Cebuano", "value": "ceb"}, {"label": "Central Atlas Tamazight", "value": "tzm"}, {"label": "Central Dusun", "value": "dtp"}, {"label": "Central Kurdish", "value": "ckb"}, {"label": "Central Yupik", "value": "esu"}, 
                                             {"label": "Chadian Arabic", "value": "shu"}, {"label": "Chagatai", "value": "chg"}, {"label": "Chamorro", "value": "ch"}, {"label": "Chechen", "value": "ce"}, {"label": "Cherokee", "value": "chr"}, {"label": "Cheyenne", "value": "chy"}, {"label": "Chibcha", "value": "chb"}, {"label": "Chiga", "value": "cgg"}, {"label": "Chimborazo Highland Quichua", "value": "qug"}, {"label": "Chinese", "value": "zh"}, 
                                             {"label": "Chinook Jargon", "value": "chn"}, {"label": "Chipewyan", "value": "chp"}, {"label": "Choctaw", "value": "cho"}, {"label": "Church Slavic", "value": "cu"}, {"label": "Chuukese", "value": "chk"}, {"label": "Chuvash", "value": "cv"}, {"label": "Classical Newari", "value": "nwc"}, {"label": "Classical Syriac", "value": "syc"}, {"label": "Colognian", "value": "ksh"}, {"label": "Comorian", "value": "swb"}, 
                                             {"label": "Congo Swahili", "value": "swc"}, {"label": "Coptic", "value": "cop"}, {"label": "Cornish", "value": "kw"}, {"label": "Corsican", "value": "co"}, {"label": "Cree", "value": "cr"}, {"label": "Creek", "value": "mus"}, {"label": "Crimean Turkish", "value": "crh"}, {"label": "Croatian", "value": "hr"}, {"label": "Czech", "value": "cs"}, {"label": "Dakota", "value": "dak"}, 
                                             {"label": "Danish", "value": "da"}, {"label": "Dargwa", "value": "dar"}, {"label": "Dazaga", "value": "dzg"}, {"label": "Delaware", "value": "del"}, {"label": "Dinka", "value": "din"}, {"label": "Divehi", "value": "dv"}, {"label": "Dogri", "value": "doi"}, {"label": "Dogrib", "value": "dgr"}, {"label": "Duala", "value": "dua"}, {"label": "Dutch", "value": "nl"}, 
                                             {"label": "Dyula", "value": "dyu"}, {"label": "Dzongkha", "value": "dz"}, {"label": "Eastern Frisian", "value": "frs"}, {"label": "Efik", "value": "efi"}, {"label": "Egyptian Arabic", "value": "arz"}, {"label": "Ekajuk", "value": "eka"}, {"label": "Elamite", "value": "elx"}, {"label": "Embu", "value": "ebu"}, {"label": "Emilian", "value": "egl"}, {"label": "English", "value": "en"}, 
                                             {"label": "Erzya", "value": "myv"}, {"label": "Esperanto", "value": "eo"}, {"label": "Estonian", "value": "et"}, {"label": "Ewe", "value": "ee"}, {"label": "Ewondo", "value": "ewo"}, {"label": "Extremaduran", "value": "ext"}, {"label": "Fang", "value": "fan"}, {"label": "Fanti", "value": "fat"}, {"label": "Faroese", "value": "fo"}, {"label": "Fiji Hindi", "value": "hif"}, 
                                             {"label": "Fijian", "value": "fj"}, {"label": "Filipino", "value": "fil"}, {"label": "Finnish", "value": "fi"}, {"label": "Fon", "value": "fon"}, {"label": "Frafra", "value": "gur"}, {"label": "French", "value": "fr"}, {"label": "Friulian", "value": "fur"}, {"label": "Fulah", "value": "ff"}, {"label": "Ga", "value": "gaa"}, {"label": "Gagauz", "value": "gag"}, 
                                             {"label": "Galician", "value": "gl"}, {"label": "Gan Chinese", "value": "gan"}, {"label": "Ganda", "value": "lg"}, {"label": "Gayo", "value": "gay"}, {"label": "Gbaya", "value": "gba"}, {"label": "Geez", "value": "gez"}, {"label": "Georgian", "value": "ka"}, {"label": "German", "value": "de"}, {"label": "Gheg Albanian", "value": "aln"}, {"label": "Ghomala", "value": "bbj"}, 
                                             {"label": "Gilaki", "value": "glk"}, {"label": "Gilbertese", "value": "gil"}, {"label": "Goan Konkani", "value": "gom"}, {"label": "Gondi", "value": "gon"}, {"label": "Gorontalo", "value": "gor"}, {"label": "Gothic", "value": "got"}, {"label": "Grebo", "value": "grb"}, {"label": "Greek", "value": "el"}, {"label": "Guarani", "value": "gn"}, {"label": "Gujarati", "value": "gu"}, 
                                             {"label": "Gusii", "value": "guz"}, {"label": "Gwich\u02bcin", "value": "gwi"}, {"label": "Haida", "value": "hai"}, {"label": "Haitian Creole", "value": "ht"}, {"label": "Hakka Chinese", "value": "hak"}, {"label": "Hausa", "value": "ha"}, {"label": "Hawaiian", "value": "haw"}, {"label": "Hebrew", "value": "he"}, {"label": "Herero", "value": "hz"}, {"label": "Hiligaynon", "value": "hil"}, 
                                             {"label": "Hindi", "value": "hi"}, {"label": "Hiri Motu", "value": "ho"}, {"label": "Hittite", "value": "hit"}, {"label": "Hmong", "value": "hmn"}, {"label": "Hungarian", "value": "hu"}, {"label": "Hupa", "value": "hup"}, {"label": "Iban", "value": "iba"}, {"label": "Ibibio", "value": "ibb"}, {"label": "Icelandic", "value": "is"}, {"label": "Ido", "value": "io"}, 
                                             {"label": "Igbo", "value": "ig"}, {"label": "Iloko", "value": "ilo"}, {"label": "Inari Sami", "value": "smn"}, {"label": "Indonesian", "value": "id"}, {"label": "Ingrian", "value": "izh"}, {"label": "Ingush", "value": "inh"}, {"label": "Interlingua", "value": "ia"}, {"label": "Interlingue", "value": "ie"}, {"label": "Inuktitut", "value": "iu"}, {"label": "Inupiaq", "value": "ik"}, 
                                             {"label": "Irish", "value": "ga"}, {"label": "Italian", "value": "it"}, {"label": "Jamaican Creole English", "value": "jam"}, {"label": "Japanese", "value": "ja"}, {"label": "Javanese", "value": "jv"}, {"label": "Jju", "value": "kaj"}, {"label": "Jola-Fonyi", "value": "dyo"}, {"label": "Judeo-Arabic", "value": "jrb"}, {"label": "Judeo-Persian", "value": "jpr"}, {"label": "Jutish", "value": "jut"}, 
                                             {"label": "Kabardian", "value": "kbd"}, {"label": "Kabuverdianu", "value": "kea"}, {"label": "Kabyle", "value": "kab"}, {"label": "Kachin", "value": "kac"}, {"label": "Kaingang", "value": "kgp"}, {"label": "Kako", "value": "kkj"}, {"label": "Kalaallisut", "value": "kl"}, {"label": "Kalenjin", "value": "kln"}, {"label": "Kalmyk", "value": "xal"}, {"label": "Kamba", "value": "kam"}, 
                                             {"label": "Kanembu", "value": "kbl"}, {"label": "Kannada", "value": "kn"}, {"label": "Kanuri", "value": "kr"}, {"label": "Kara-Kalpak", "value": "kaa"}, {"label": "Karachay-Balkar", "value": "krc"}, {"label": "Karelian", "value": "krl"}, {"label": "Kashmiri", "value": "ks"}, {"label": "Kashubian", "value": "csb"}, {"label": "Kawi", "value": "kaw"}, {"label": "Kazakh", "value": "kk"}, 
                                             {"label": "Kenyang", "value": "ken"}, {"label": "Khasi", "value": "kha"}, {"label": "Khmer", "value": "km"}, {"label": "Khotanese", "value": "kho"}, {"label": "Khowar", "value": "khw"}, {"label": "Kikuyu", "value": "ki"}, {"label": "Kimbundu", "value": "kmb"}, {"label": "Kinaray-a", "value": "krj"}, {"label": "Kinyarwanda", "value": "rw"}, {"label": "Kirmanjki", "value": "kiu"}, 
                                             {"label": "Klingon", "value": "tlh"}, {"label": "Kom", "value": "bkm"}, {"label": "Komi", "value": "kv"}, {"label": "Komi-Permyak", "value": "koi"}, {"label": "Kongo", "value": "kg"}, {"label": "Konkani", "value": "kok"}, {"label": "Korean", "value": "ko"}, {"label": "Koro", "value": "kfo"}, {"label": "Kosraean", "value": "kos"}, {"label": "Kotava", "value": "avk"}, 
                                             {"label": "Koyra Chiini", "value": "khq"}, {"label": "Koyraboro Senni", "value": "ses"}, {"label": "Kpelle", "value": "kpe"}, {"label": "Krio", "value": "kri"}, {"label": "Kuanyama", "value": "kj"}, {"label": "Kumyk", "value": "kum"}, {"label": "Kurdish", "value": "ku"}, {"label": "Kurukh", "value": "kru"}, {"label": "Kutenai", "value": "kut"}, {"label": "Kwasio", "value": "nmg"}, 
                                             {"label": "Kyrgyz", "value": "ky"}, {"label": "K\u02bciche\u02bc", "value": "quc"}, {"label": "Ladino", "value": "lad"}, {"label": "Lahnda", "value": "lah"}, {"label": "Lakota", "value": "lkt"}, {"label": "Lamba", "value": "lam"}, {"label": "Langi", "value": "lag"}, {"label": "Lao", "value": "lo"}, {"label": "Latgalian", "value": "ltg"}, {"label": "Latin", "value": "la"}, 
                                             {"label": "Latvian", "value": "lv"}, {"label": "Laz", "value": "lzz"}, {"label": "Lezghian", "value": "lez"}, {"label": "Ligurian", "value": "lij"}, {"label": "Limburgish", "value": "li"}, {"label": "Lingala", "value": "ln"}, {"label": "Lingua Franca Nova", "value": "lfn"}, {"label": "Literary Chinese", "value": "lzh"}, {"label": "Lithuanian", "value": "lt"}, {"label": "Livonian", "value": "liv"}, 
                                             {"label": "Lojban", "value": "jbo"}, {"label": "Lombard", "value": "lmo"}, {"label": "Low German", "value": "nds"}, {"label": "Lower Silesian", "value": "sli"}, {"label": "Lower Sorbian", "value": "dsb"}, {"label": "Lozi", "value": "loz"}, {"label": "Luba-Katanga", "value": "lu"}, {"label": "Luba-Lulua", "value": "lua"}, {"label": "Luiseno", "value": "lui"}, {"label": "Lule Sami", "value": "smj"}, 
                                             {"label": "Lunda", "value": "lun"}, {"label": "Luo", "value": "luo"}, {"label": "Luxembourgish", "value": "lb"}, {"label": "Luyia", "value": "luy"}, {"label": "Maba", "value": "mde"}, {"label": "Macedonian", "value": "mk"}, {"label": "Machame", "value": "jmc"}, {"label": "Madurese", "value": "mad"}, {"label": "Mafa", "value": "maf"}, {"label": "Magahi", "value": "mag"}, 
                                             {"label": "Main-Franconian", "value": "vmf"}, {"label": "Maithili", "value": "mai"}, {"label": "Makasar", "value": "mak"}, {"label": "Makhuwa-Meetto", "value": "mgh"}, {"label": "Makonde", "value": "kde"}, {"label": "Malagasy", "value": "mg"}, {"label": "Malay", "value": "ms"}, {"label": "Malayalam", "value": "ml"}, {"label": "Maltese", "value": "mt"}, {"label": "Manchu", "value": "mnc"}, 
                                             {"label": "Mandar", "value": "mdr"}, {"label": "Mandingo", "value": "man"}, {"label": "Manipuri", "value": "mni"}, {"label": "Manx", "value": "gv"}, {"label": "Maori", "value": "mi"}, {"label": "Mapuche", "value": "arn"}, {"label": "Marathi", "value": "mr"}, {"label": "Mari", "value": "chm"}, {"label": "Marshallese", "value": "mh"}, {"label": "Marwari", "value": "mwr"}, 
                                             {"label": "Masai", "value": "mas"}, {"label": "Mazanderani", "value": "mzn"}, {"label": "Medumba", "value": "byv"}, {"label": "Mende", "value": "men"}, {"label": "Mentawai", "value": "mwv"}, {"label": "Meru", "value": "mer"}, {"label": "Meta\u02bc", "value": "mgo"}, {"label": "Micmac", "value": "mic"}, {"label": "Middle Dutch", "value": "dum"}, {"label": "Middle English", "value": "enm"}, 
                                             {"label": "Middle French", "value": "frm"}, {"label": "Middle High German", "value": "gmh"}, {"label": "Middle Irish", "value": "mga"}, {"label": "Min Nan Chinese", "value": "nan"}, {"label": "Minangkabau", "value": "min"}, {"label": "Mingrelian", "value": "xmf"}, {"label": "Mirandese", "value": "mwl"}, {"label": "Mizo", "value": "lus"}, {"label": "Mohawk", "value": "moh"}, {"label": "Moksha", "value": "mdf"}, 
                                             {"label": "Mongo", "value": "lol"}, {"label": "Mongolian", "value": "mn"}, {"label": "Morisyen", "value": "mfe"}, {"label": "Moroccan Arabic", "value": "ary"}, {"label": "Mossi", "value": "mos"}, {"label": "Multiple Languages", "value": "mul"}, {"label": "Mundang", "value": "mua"}, {"label": "Muslim Tat", "value": "ttt"}, {"label": "Myene", "value": "mye"}, {"label": "Nama", "value": "naq"}, 
                                             {"label": "Nauru", "value": "na"}, {"label": "Navajo", "value": "nv"}, {"label": "Ndonga", "value": "ng"}, {"label": "Neapolitan", "value": "nap"}, {"label": "Nepali", "value": "ne"}, {"label": "Newari", "value": "new"}, {"label": "Ngambay", "value": "sba"}, {"label": "Ngiemboon", "value": "nnh"}, {"label": "Ngomba", "value": "jgo"}, {"label": "Nheengatu", "value": "yrl"}, 
                                             {"label": "Nias", "value": "nia"}, {"label": "Niuean", "value": "niu"}, {"label": "No linguistic content", "value": "zxx"}, {"label": "Nogai", "value": "nog"}, {"label": "North Ndebele", "value": "nd"}, {"label": "Northern Frisian", "value": "frr"}, {"label": "Northern Luri", "value": "lrc"}, {"label": "Northern Sami", "value": "se"}, {"label": "Northern Sotho", "value": "nso"}, {"label": "Norwegian", "value": "no"}, 
                                             {"label": "Norwegian Bokm\u00e5l", "value": "nb"}, {"label": "Norwegian Nynorsk", "value": "nn"}, {"label": "Novial", "value": "nov"}, {"label": "Nuer", "value": "nus"}, {"label": "Nyamwezi", "value": "nym"}, {"label": "Nyanja", "value": "ny"}, {"label": "Nyankole", "value": "nyn"}, {"label": "Nyasa Tonga", "value": "tog"}, {"label": "Nyoro", "value": "nyo"}, {"label": "Nzima", "value": "nzi"}, 
                                             {"label": "N\u2019Ko", "value": "nqo"}, {"label": "Occitan", "value": "oc"}, {"label": "Ojibwa", "value": "oj"}, {"label": "Old English", "value": "ang"}, {"label": "Old French", "value": "fro"}, {"label": "Old High German", "value": "goh"}, {"label": "Old Irish", "value": "sga"}, {"label": "Old Norse", "value": "non"}, {"label": "Old Persian", "value": "peo"}, {"label": "Old Proven\u00e7al", "value": "pro"}, 
                                             {"label": "Oriya", "value": "or"}, {"label": "Oromo", "value": "om"}, {"label": "Osage", "value": "osa"}, {"label": "Ossetic", "value": "os"}, {"label": "Ottoman Turkish", "value": "ota"}, {"label": "Pahlavi", "value": "pal"}, {"label": "Palatine German", "value": "pfl"}, {"label": "Palauan", "value": "pau"}, {"label": "Pali", "value": "pi"}, {"label": "Pampanga", "value": "pam"}, 
                                             {"label": "Pangasinan", "value": "pag"}, {"label": "Papiamento", "value": "pap"}, {"label": "Pashto", "value": "ps"}, {"label": "Pennsylvania German", "value": "pdc"}, {"label": "Persian", "value": "fa"}, {"label": "Phoenician", "value": "phn"}, {"label": "Picard", "value": "pcd"}, {"label": "Piedmontese", "value": "pms"}, {"label": "Plautdietsch", "value": "pdt"}, {"label": "Pohnpeian", "value": "pon"}, 
                                             {"label": "Polish", "value": "pl"}, {"label": "Pontic", "value": "pnt"}, {"label": "Portuguese", "value": "pt"}, {"label": "Prussian", "value": "prg"}, {"label": "Punjabi", "value": "pa"}, {"label": "Quechua", "value": "qu"}, {"label": "Rajasthani", "value": "raj"}, {"label": "Rapanui", "value": "rap"}, {"label": "Rarotongan", "value": "rar"}, {"label": "Riffian", "value": "rif"}, 
                                             {"label": "Romagnol", "value": "rgn"}, {"label": "Romanian", "value": "ro"}, {"label": "Romansh", "value": "rm"}, {"label": "Romany", "value": "rom"}, {"label": "Rombo", "value": "rof"}, {"label": "Root", "value": "root"}, {"label": "Rotuman", "value": "rtm"}, {"label": "Roviana", "value": "rug"}, {"label": "Rundi", "value": "rn"}, {"label": "Russian", "value": "ru"}, 
                                             {"label": "Rusyn", "value": "rue"}, {"label": "Rwa", "value": "rwk"}, {"label": "Saho", "value": "ssy"}, {"label": "Sakha", "value": "sah"}, {"label": "Samaritan Aramaic", "value": "sam"}, {"label": "Samburu", "value": "saq"}, {"label": "Samoan", "value": "sm"}, {"label": "Samogitian", "value": "sgs"}, {"label": "Sandawe", "value": "sad"}, {"label": "Sango", "value": "sg"}, 
                                             {"label": "Sangu", "value": "sbp"}, {"label": "Sanskrit", "value": "sa"}, {"label": "Santali", "value": "sat"}, {"label": "Sardinian", "value": "sc"}, {"label": "Sasak", "value": "sas"}, {"label": "Sassarese Sardinian", "value": "sdc"}, {"label": "Saterland Frisian", "value": "stq"}, {"label": "Saurashtra", "value": "saz"}, {"label": "Scots", "value": "sco"}, {"label": "Scottish Gaelic", "value": "gd"}, 
                                             {"label": "Selayar", "value": "sly"}, {"label": "Selkup", "value": "sel"}, {"label": "Sena", "value": "seh"}, {"label": "Seneca", "value": "see"}, {"label": "Serbian", "value": "sr"}, {"label": "Serbo-Croatian", "value": "sh"}, {"label": "Serer", "value": "srr"}, {"label": "Seri", "value": "sei"}, {"label": "Shambala", "value": "ksb"}, {"label": "Shan", "value": "shn"}, 
                                             {"label": "Shona", "value": "sn"}, {"label": "Sichuan Yi", "value": "ii"}, {"label": "Sicilian", "value": "scn"}, {"label": "Sidamo", "value": "sid"}, {"label": "Siksika", "value": "bla"}, {"label": "Silesian", "value": "szl"}, {"label": "Sindhi", "value": "sd"}, {"label": "Sinhala", "value": "si"}, {"label": "Skolt Sami", "value": "sms"}, {"label": "Slave", "value": "den"}, 
                                             {"label": "Slovak", "value": "sk"}, {"label": "Slovenian", "value": "sl"}, {"label": "Soga", "value": "xog"}, {"label": "Sogdien", "value": "sog"}, {"label": "Somali", "value": "so"}, {"label": "Soninke", "value": "snk"}, {"label": "South Ndebele", "value": "nr"}, {"label": "Southern Altai", "value": "alt"}, {"label": "Southern Kurdish", "value": "sdh"}, {"label": "Southern Sami", "value": "sma"}, 
                                             {"label": "Southern Sotho", "value": "st"}, {"label": "Spanish", "value": "es"}, {"label": "Sranan Tongo", "value": "srn"}, {"label": "Standard Moroccan Tamazight", "value": "zgh"}, {"label": "Sukuma", "value": "suk"}, {"label": "Sumerian", "value": "sux"}, {"label": "Sundanese", "value": "su"}, {"label": "Susu", "value": "sus"}, {"label": "Swahili", "value": "sw"}, {"label": "Swati", "value": "ss"}, 
                                             {"label": "Swedish", "value": "sv"}, {"label": "Swiss German", "value": "gsw"}, {"label": "Syriac", "value": "syr"}, {"label": "Tachelhit", "value": "shi"}, {"label": "Tagalog", "value": "tl"}, {"label": "Tahitian", "value": "ty"}, {"label": "Taita", "value": "dav"}, {"label": "Tajik", "value": "tg"}, {"label": "Talysh", "value": "tly"}, {"label": "Tamashek", "value": "tmh"}, 
                                             {"label": "Tamil", "value": "ta"}, {"label": "Taroko", "value": "trv"}, {"label": "Tasawaq", "value": "twq"}, {"label": "Tatar", "value": "tt"}, {"label": "Telugu", "value": "te"}, {"label": "Tereno", "value": "ter"}, {"label": "Teso", "value": "teo"}, {"label": "Tetum", "value": "tet"}, {"label": "Thai", "value": "th"}, {"label": "Tibetan", "value": "bo"}, 
                                             {"label": "Tigre", "value": "tig"}, {"label": "Tigrinya", "value": "ti"}, {"label": "Timne", "value": "tem"}, {"label": "Tiv", "value": "tiv"}, {"label": "Tlingit", "value": "tli"}, {"label": "Tok Pisin", "value": "tpi"}, {"label": "Tokelau", "value": "tkl"}, {"label": "Tongan", "value": "to"}, {"label": "Tornedalen Finnish", "value": "fit"}, {"label": "Tsakhur", "value": "tkr"}, 
                                             {"label": "Tsakonian", "value": "tsd"}, {"label": "Tsimshian", "value": "tsi"}, {"label": "Tsonga", "value": "ts"}, {"label": "Tswana", "value": "tn"}, {"label": "Tulu", "value": "tcy"}, {"label": "Tumbuka", "value": "tum"}, {"label": "Tunisian Arabic", "value": "aeb"}, {"label": "Turkish", "value": "tr"}, {"label": "Turkmen", "value": "tk"}, {"label": "Turoyo", "value": "tru"}, 
                                             {"label": "Tuvalu", "value": "tvl"}, {"label": "Tuvinian", "value": "tyv"}, {"label": "Twi", "value": "tw"}, {"label": "Tyap", "value": "kcg"}, {"label": "Udmurt", "value": "udm"}, {"label": "Ugaritic", "value": "uga"}, {"label": "Ukrainian", "value": "uk"}, {"label": "Umbundu", "value": "umb"}, {"label": "Unknown Language", "value": "und"}, {"label": "Upper Sorbian", "value": "hsb"}, 
                                             {"label": "Urdu", "value": "ur"}, {"label": "Uyghur", "value": "ug"}, {"label": "Uzbek", "value": "uz"}, {"label": "Vai", "value": "vai"}, {"label": "Venda", "value": "ve"}, {"label": "Venetian", "value": "vec"}, {"label": "Veps", "value": "vep"}, {"label": "Vietnamese", "value": "vi"}, {"label": "Volap\u00fck", "value": "vo"}, {"label": "Votic", "value": "vot"}, 
                                             {"label": "Vunjo", "value": "vun"}, {"label": "V\u00f5ro", "value": "vro"}, {"label": "Walloon", "value": "wa"}, {"label": "Walser", "value": "wae"}, {"label": "Waray", "value": "war"}, {"label": "Warlpiri", "value": "wbp"}, {"label": "Washo", "value": "was"}, {"label": "Wayuu", "value": "guc"}, {"label": "Welsh", "value": "cy"}, {"label": "West Flemish", "value": "vls"}, 
                                             {"label": "Western Balochi", "value": "bgn"}, {"label": "Western Frisian", "value": "fy"}, {"label": "Western Mari", "value": "mrj"}, {"label": "Wolaytta", "value": "wal"}, {"label": "Wolof", "value": "wo"}, {"label": "Wu Chinese", "value": "wuu"}, {"label": "Xhosa", "value": "xh"}, {"label": "Xiang Chinese", "value": "hsn"}, {"label": "Yangben", "value": "yav"}, {"label": "Yao", "value": "yao"}, 
                                             {"label": "Yapese", "value": "yap"}, {"label": "Yemba", "value": "ybb"}, {"label": "Yiddish", "value": "yi"}, {"label": "Yoruba", "value": "yo"}, {"label": "Zapotec", "value": "zap"}, {"label": "Zarma", "value": "dje"}, {"label": "Zaza", "value": "zza"}, {"label": "Zeelandic", "value": "zea"}, {"label": "Zenaga", "value": "zen"}, {"label": "Zhuang", "value": "za"}, 
                                             {"label": "Zoroastrian Dari", "value": "gbz"}, {"label": "Zulu", "value": "zu"}, {"label": "Zuni", "value": "zun"}],
                                 "widget": "select", "highlight": "",
                                 "javascript": "var highlights = '${highlight}';if(highlights.trim()!=''){highlights=highlights.split(',');}if(highlights.length>0){var marker=question.find('select option:first-child()');for(var idx=0;idx<highlights.length;idx++){var elem=question.find('option[value=' + highlights[idx].trim() + ']');if(elem.length>0){marker.after(elem);marker=elem;}}marker.after('<option value=\\\\'\\\\'>------------------------------</option>');}",
                                 "generates_response": true}''',
                                   'backend': '''{"fields": [{"name": "name", "type": "text", "title": "Unique Name", "validation": {"type": "unicode", "not_empty": true}},
                                           {"name": "title", "type": "text", "title": "Title", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "required", "type": "checkbox", "title": "Required", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "help", "type": "textarea", "title": "Help", "extra_attrs": {"style": "height: 5rem"}, "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}},
                                           {"name": "allow_multiple", "type": "checkbox", "title": "Allow multiple Answers", "validation": {"type": "boolean", "if_empty": "", "if_missing": ""}},
                                           {"name": "highlight", "type": "text", "title": "Highlight these Languages (language codes separated by commas)", "validation": {"type": "unicode", "if_empty": "", "if_missing": ""}}
                                           ]}'''}}


def upgrade():
    insp = sa.engine.reflection.Inspector.from_engine(op.get_bind())
    metadata.bind = op.get_bind()
    # Update to the new Experiment model
    if 'surveys' in insp.get_table_names():
        op.rename_table('surveys', 'experiments')
    if 'surveys_users_owner_fk' in [v['name'] for v in insp.get_foreign_keys('experiments')]:
        op.drop_constraint('surveys_users_owner_fk', 'experiments')
    if 'surveys_owned_by_fkey' in [v['name'] for v in insp.get_foreign_keys('experiments')]:
        op.drop_constraint('surveys_owned_by_fkey', 'experiments')
    if 'experiments_users_owner_fk' not in [v['name'] for v in insp.get_foreign_keys('experiments')]:
        op.create_foreign_key('experiments_users_owner_fk', 'experiments', 'users', ['owned_by'], ['id'])
    # Update to the new Pages model I
    if 'qsheets' in insp.get_table_names():
        op.rename_table('qsheets', 'pages')
    # Update to the new Questions model I
    if 'qsheet_id' in [v['name'] for v in insp.get_columns('questions')]:
        op.alter_column('questions', 'qsheet_id', new_column_name='page_id')
    # Update to the new Transition model
    if 'qsheet_transitions' in insp.get_table_names():
        op.rename_table('qsheet_transitions', 'transitions')
    if 'survey_id' in [v['name'] for v in insp.get_columns('pages')]:
        op.alter_column('pages', 'survey_id', new_column_name='experiment_id')
    if 'attributes' not in [v['name'] for v in insp.get_columns('transitions')]:
        op.add_column('transitions', sa.Column('attributes', sa.UnicodeText()))
        for transition in op.get_bind().execute(transitions.select()):
            attributes = {}
            if transition[3] and transition[3].strip():
                attrs = json.loads(transition[3])
                attributes['condition'] = {}
                if attrs['type'] == 'permutation':
                    attributes['condition']['type'] = 'latinsquare'
                elif attrs['type'] == 'dataset':
                    attributes['condition']['type'] = 'dataset'
                elif attrs['type'] == 'answer':
                    attributes['condition']['type'] = 'answer'
                    attributes['condition']['value'] = attrs['answer']
                    p, q = attrs['question'].split('.')
                    exp_id = op.get_bind().execute(sa.select([pages.c.experiment_id]).where(pages.c.id == transition[1])).first()[0]
                    p = op.get_bind().execute(sa.select([pages.c.id]).where(sa.and_(pages.c.name == p, pages.c.experiment_id == exp_id))).first()
                    q = op.get_bind().execute(sa.select([questions.c.id]).where(sa.and_(questions.c.page_id == p[0], questions.c.name == q))).first()
                    attributes['condition']['page'] = p[0]
                    attributes['condition']['question'] = q[0]
            op.get_bind().execute(transitions.update().values(attributes=json.dumps(attributes)).where(transitions.c.id == transition[0]))
        op.drop_column('transitions', '_condition')
        op.drop_column('transitions', '_action')
    # Update to the new DataSets model I
    if 'attributes' not in [v['name'] for v in insp.get_columns('data_sets')]:
        op.add_column('data_sets', sa.Column('attributes', sa.UnicodeText()))
    # Update to the new Page model II
    if 'attributes' not in [v['name'] for v in insp.get_columns('pages')]:
        op.add_column('pages', sa.Column('attributes', sa.UnicodeText()))
        for page in op.get_bind().execute(pages.select()):
            attributes = {}
            for attr in op.get_bind().execute(qsheet_attributes.select().where(qsheet_attributes.c.qsheet_id == page[0])):
                if attr[2] == 'show-question-numbers':
                    if attr[3] == 'yes':
                        attributes['number_questions'] = True
                    else:
                        attributes['number_questions'] = False
                elif attr[2] == 'data-items':
                    if page[1] is not None and attr[3] != '0':
                        if op.get_bind().execute(data_sets.select().where(data_sets.c.id == page[1])).first() is not None:
                            if 'data' not in attributes:
                                attributes['data'] = {}
                            attributes['data']['item_count'] = int(attr[3])
                elif attr[2] == 'control-items':
                    if page[1] is not None and attr[3] != '0':
                        if op.get_bind().execute(data_sets.select().where(data_sets.c.id == page[1])).first() is not None:
                            if 'data' not in attributes:
                                attributes['data'] = {}
                            attributes['data']['control_count'] = int(attr[3])
                elif attr[2] == 'repeat':
                    if attr[3] == 'repeat':
                        op.get_bind().execute(transitions.insert().values(source_id=page[0], target_id=page[0], attributes=json.dumps({'condition': {'type': 'dataset'}}), order=-1))
            op.get_bind().execute(pages.update().values(attributes=json.dumps(attributes)).where(pages.c.id == page[0]))
    if 'qsheet_attributes' in insp.get_table_names():
        op.drop_table('qsheet_attributes')
    # Update to the new Questions model II
    if 'name' in [v['name'] for v in insp.get_columns('questions')]:
        for question in op.get_bind().execute(questions.select()):
            attributes = {}
            if question[2]:
                attributes['name'] = question[2]
            if question[3] and question[3].strip():
                attributes['title'] = question[3].strip()
            if question[4]:
                attributes['required'] = True
            else:
                attributes['required'] = False
            if question[5] and question[5].strip():
                attributes['help'] = question[5].strip()
            for attr in op.get_bind().execute(sa.select([question_complex_attributes.c.key, question_attributes.c.key, question_attributes.c.value]).select_from(question_complex_attributes.join(question_attributes, question_complex_attributes.c.id == question_attributes.c.question_group_id)).where(question_complex_attributes.c.question_id == question[0]).order_by(question_complex_attributes.c.order, question_attributes.c.order)):
                if attr[0] == 'text' and attr[1] == 'text':
                    attributes['text'] = attr[2]
                elif attr[0] == 'answer' and attr[1] == 'value':
                    if 'answer_values' not in attributes:
                        attributes['answer_values'] = []
                    attributes['answer_values'].append(attr[2])
                elif attr[0] == 'answer' and attr[1] == 'label':
                    if 'answer_labels' not in attributes:
                        attributes['answer_labels'] = []
                    attributes['answer_labels'].append(attr[2])
                elif attr[0] == 'subquestion' and attr[1] == 'name':
                    if 'question_names' not in attributes:
                        attributes['question_names'] = []
                    attributes['question_names'].append(attr[2])
                elif attr[0] == 'subquestion' and attr[1] == 'label':
                    if 'question_labels' not in attributes:
                        attributes['question_labels'] = []
                    attributes['question_labels'].append(attr[2])
                elif attr[0] == 'further' and attr[1] == 'before_label':
                    attributes['before_label'] = attr[2]
                elif attr[0] == 'further' and attr[1] == 'after_label':
                    attributes['after_label'] = attr[2]
                elif attr[0] == 'further' and attr[1] == 'allow_other':
                    if attr[2] == 'yes':
                        attributes['allow_other'] = True
                    else:
                        attributes['allow_other'] = False
                elif attr[0] == 'further' and attr[1] == 'subtype':
                    attributes['widget'] = attr[2]
                elif attr[0] == 'further' and attr[1] == 'allow_multiple':
                    if attr[2] == 'True':
                        attributes['allow_multiple'] = True
                    else:
                        attributes['allow_multiple'] = False
                elif attr[0] == 'further' and attr[1] == 'value':
                    if attr[2] and attr[2].strip():
                        attributes['answer_values'] = [attr[2]]
                elif attr[0] == 'further' and attr[1] == 'label':
                    if attr[2] and attr[2].strip():
                        attributes['answer_labels'] = [attr[2]]
                elif attr[0] == 'further' and attr[1] == 'priority':
                    if attr[2] and attr[2].strip():
                        attributes['highlight'] = attr[2]
                elif attr[0] == 'further' and attr[1] == 'max':
                    if attr[2] and attr[2].strip():
                        attributes['max'] = attr[2]
                elif attr[0] == 'further' and attr[1] == 'min':
                    if attr[2] and attr[2].strip():
                        attributes['min'] = attr[2]
                elif attr[0] == 'further' and attr[1] == 'timeout':
                    if attr[2] and attr[2].strip():
                        attributes['delay'] = attr[2]
            if 'answer_values' in attributes and 'answer_labels' in attributes:
                attributes['answers'] = [{'value': p[0], 'label': p[1]} for p in zip(attributes['answer_values'], attributes['answer_labels'])]
                del attributes['answer_values']
                del attributes['answer_labels']
            if 'question_names' in attributes and 'question_labels' in attributes:
                attributes['questions'] = [{'name': p[0], 'label': p[1]} for p in zip(attributes['question_names'], attributes['question_labels'])]
                del attributes['question_names']
                del attributes['question_labels']
            op.get_bind().execute(questions.update().values(attributes=json.dumps(attributes)).where(questions.c.id == question[0]))
        op.drop_column('questions', 'name')
        op.drop_column('questions', 'title')
        op.drop_column('questions', 'required')
        op.drop_column('questions', 'help')
    if 'question_attributes' in insp.get_table_names():
        op.drop_table('question_attributes')
    if 'question_complex_attributes' in insp.get_table_names():
        op.drop_table('question_complex_attributes')
    # Update to the new Question Type Groups model I
    op.get_bind().execute(question_type_groups.update().values(name='ess:builtins', title='Builtin Questions').where(question_type_groups.c.name == 'core'))
    builtins_id = op.get_bind().execute(question_type_groups.select().where(question_type_groups.c.name == 'ess:builtins')).first()[0]
    op.get_bind().execute(question_type_groups.update().values(name='ess:core', title='General').where(sa.and_(question_type_groups.c.name == 'text', question_type_groups.c.parent_id == builtins_id)))
    op.get_bind().execute(question_type_groups.update().values(name='ess:js', title='JavaScript').where(sa.and_(question_type_groups.c.name == 'choice', question_type_groups.c.parent_id == builtins_id)))
    op.get_bind().execute(question_type_groups.update().values(name='ess:international', title='International').where(sa.and_(question_type_groups.c.name == 'hidden', question_type_groups.c.parent_id == builtins_id)))
    # Update to the new Question Type model
    if 'attributes' in [v['name'] for v in insp.get_columns('question_types')]:
        op.drop_column('question_types', 'attributes')
    if 'dbschema' in [v['name'] for v in insp.get_columns('question_types')]:
        op.drop_column('question_types', 'dbschema')
    if 'answer_validation' in [v['name'] for v in insp.get_columns('question_types')]:
        op.drop_column('question_types', 'answer_validation')
    core_id = op.get_bind().execute(question_type_groups.select().where(question_type_groups.c.name == 'ess:core')).first()[0]
    js_id = op.get_bind().execute(question_type_groups.select().where(question_type_groups.c.name == 'ess:js')).first()[0]
    int_id = op.get_bind().execute(question_type_groups.select().where(question_type_groups.c.name == 'ess:international')).first()[0]
    other_id = op.get_bind().execute(question_type_groups.select().where(sa.and_(question_type_groups.c.name == 'other', question_type_groups.c.parent_id == builtins_id))).first()
    if other_id:
        other_id = other_id[0]
    for question_type in op.get_bind().execute(question_types.select()):
        if question_type[1] == 'text' and question_type[5] == core_id:
            op.get_bind().execute(question_types.update().values(order=0, **NEW_QUESTION_TYPES['text']).where(question_types.c.id == question_type[0]))
        elif question_type[1] == 'short_text' and question_type[5] == core_id:
            op.get_bind().execute(question_types.update().values(name='simple_input', title='Basic Input', order=1, **NEW_QUESTION_TYPES['simple_input']).where(question_types.c.id == question_type[0]))
        elif question_type[1] in ['long_text', 'number', 'email', 'url', 'date', 'time', 'datetime', 'month'] and question_type[5] == core_id:
            replace_id = op.get_bind().execute(question_types.select().where(sa.and_(sa.or_(question_types.c.name == 'simple_input', question_types.c.name == 'short_text'), question_types.c.group_id == core_id))).first()[0]
            op.get_bind().execute(questions.update().values(type_id=replace_id).where(questions.c.type_id == question_type[0]))
            op.get_bind().execute(question_types.delete().where(question_types.c.id == question_type[0]))
        elif question_type[1] == 'single_choice' and question_type[5] == js_id:
            op.get_bind().execute(question_types.update().values(name='select_simple_choice', title='Basic Selection', group_id=core_id, order=2, **NEW_QUESTION_TYPES['select_simple_choice']).where(question_types.c.id == question_type[0]))
        elif question_type[1] == 'multi_choice' and question_type[5] == js_id:
            replace_id = op.get_bind().execute(question_types.select().where(sa.or_(sa.and_(question_types.c.name == 'select_simple_choice', question_types.c.group_id == core_id), sa.and_(question_types.c.name == 'single_choice', question_types.c.group_id == js_id)))).first()[0]
            for question in op.get_bind().execute(sa.select([questions.c.id, questions.c.attributes]).where(questions.c.type_id == question_type[0])):
                attr = json.loads(question[1])
                attr['allow_multiple'] = True
                op.get_bind().execute(questions.update().values(type_id=replace_id, attributes=json.dumps(attr)).where(questions.c.id == question[0]))
            op.get_bind().execute(question_types.delete().where(question_types.c.id == question_type[0]))
        elif question_type[1] == 'confirm' and question_type[5] == other_id:
            replace_id = op.get_bind().execute(question_types.select().where(sa.or_(sa.and_(question_types.c.name == 'select_simple_choice', question_types.c.group_id == core_id), sa.and_(question_types.c.name == 'single_choice', question_types.c.group_id == js_id)))).first()[0]
            for question in op.get_bind().execute(sa.select([questions.c.id, questions.c.attributes]).where(questions.c.type_id == question_type[0])):
                attr = json.loads(question[1])
                attr['allow_multiple'] = True
                op.get_bind().execute(questions.update().values(type_id=replace_id, attributes=json.dumps(attr)).where(questions.c.id == question[0]))
            op.get_bind().execute(question_types.delete().where(question_types.c.id == question_type[0]))
        elif question_type[1] == 'single_choice_grid' and question_type[5] == js_id:
            op.get_bind().execute(question_types.update().values(name='select_grid_choice', title='Complex Selection', group_id=core_id, order=3, **NEW_QUESTION_TYPES['select_grid_choice']).where(question_types.c.id == question_type[0]))
        elif question_type[1] == 'multi_choice_grid' and question_type[5] == js_id:
            replace_id = op.get_bind().execute(question_types.select().where(sa.or_(sa.and_(question_types.c.name == 'select_grid_choice', question_types.c.group_id == core_id), sa.and_(question_types.c.name == 'single_choice_grid', question_types.c.group_id == js_id)))).first()[0]
            for question in op.get_bind().execute(sa.select([questions.c.id, questions.c.attributes]).where(questions.c.type_id == question_type[0])):
                attr = json.loads(question[1])
                attr['allow_multiple'] = True
                op.get_bind().execute(questions.update().values(type_id=replace_id, attributes=json.dumps(attr)).where(questions.c.id == question[0]))
            op.get_bind().execute(question_types.delete().where(question_types.c.id == question_type[0]))
        elif question_type[1] == 'ranking' and question_type[5] == other_id:
            op.get_bind().execute(question_types.update().values(group_id=core_id, order=4, **NEW_QUESTION_TYPES['ranking']).where(question_types.c.id == question_type[0]))
        elif question_type[1] == 'hidden_value' and question_type[5] == int_id:
            op.get_bind().execute(question_types.update().values(name='hidden', title='Hidden Value', group_id=core_id, order=5, **NEW_QUESTION_TYPES['hidden_value']).where(question_types.c.id == question_type[0]))
        elif question_type[1] == 'page_timer' and question_type[5] == int_id:
            op.get_bind().execute(question_types.update().values(group_id=js_id, order=0, **NEW_QUESTION_TYPES['page_timer']).where(question_types.c.id == question_type[0]))
        elif question_type[1] == 'auto_commit' and question_type[5] == int_id:
            op.get_bind().execute(question_types.update().values(name='auto_submit', title='"Automatic Page Submission"', group_id=js_id, order=1, **NEW_QUESTION_TYPES['auto_submit']).where(question_types.c.id == question_type[0]))
        elif question_type[1] == 'country' and question_type[5] == js_id:
            parent_id = op.get_bind().execute(question_types.select().where(sa.or_(sa.and_(question_types.c.name == 'select_simple_choice', question_types.c.group_id == core_id), sa.and_(question_types.c.name == 'single_choice', question_types.c.group_id == js_id)))).first()[0]
            op.get_bind().execute(question_types.update().values(parent_id=parent_id, group_id=int_id, order=1, **NEW_QUESTION_TYPES['country']).where(question_types.c.id == question_type[0]))
        elif question_type[1] == 'language' and question_type[5] == js_id:
            parent_id = op.get_bind().execute(question_types.select().where(sa.or_(sa.and_(question_types.c.name == 'select_simple_choice', question_types.c.group_id == core_id), sa.and_(question_types.c.name == 'single_choice', question_types.c.group_id == js_id)))).first()[0]
            op.get_bind().execute(question_types.update().values(parent_id=parent_id, group_id=int_id, order=0, **NEW_QUESTION_TYPES['language']).where(question_types.c.id == question_type[0]))
        elif question_type[1] == 'js_check' and question_type[5] == other_id:
            replace_id = op.get_bind().execute(question_types.select().where(sa.or_(sa.and_(question_types.c.name == 'select_grid_choice', question_types.c.group_id == core_id), sa.and_(question_types.c.name == 'single_choice_grid', question_types.c.group_id == js_id)))).first()[0]
            op.get_bind().execute(questions.update().values(type_id=replace_id).where(questions.c.type_id == question_type[0]))
            op.get_bind().execute(question_types.delete().where(question_types.c.id == question_type[0]))
    # Update to the new Question Type Groups model II
    op.get_bind().execute(question_type_groups.delete().where(sa.and_(question_type_groups.c.name == 'other', question_type_groups.c.parent_id == builtins_id)))
    # Update to the new DataSet model II
    if 'survey_id' in [v['name'] for v in insp.get_columns('data_sets')]:
        op.alter_column('data_sets', 'survey_id', new_column_name='experiment_id')
        for data_set in op.get_bind().execute(data_sets.select()):
            if data_set[1] == 'dataset':
                columns = []
                for attr in op.get_bind().execute(data_set_attribute_keys.select().where(data_set_attribute_keys.c.dataset_id == data_set[0]).order_by(data_set_attribute_keys.c.order)):
                    columns.append(attr[2])
                op.get_bind().execute(data_sets.update().values(attributes=json.dumps({'columns': columns})).where(data_sets.c.id == data_set[0]))
            elif data_set[1] == 'permutationset'or data_set[1] == 'latinsquare':
                attributes = {'columns': [],
                              'combinations': []}
                for relation in op.get_bind().execute(data_set_relations.select().where(data_set_relations.c.subject_id == data_set[0])):
                    for attr in op.get_bind().execute(data_set_attribute_keys.select().where(data_set_attribute_keys.c.dataset_id == relation[2]).order_by(data_set_attribute_keys.c.order)):
                        attributes['columns'].append(attr[2])
                    if relation[3] == 'tasks':
                        attributes['source_a'] = relation[2]
                        attributes['mode_a'] = json.loads(relation[4])['mode']
                    else:
                        attributes['source_b'] = relation[2]
                        attributes['mode_b'] = json.loads(relation[4])['mode']
                op.get_bind().execute(data_sets.update().values(type='latinsquare', attributes=json.dumps(attributes)).where(data_sets.c.id == data_set[0]))
    if 'attributes' not in [v['name'] for v in insp.get_columns('data_items')]:
        op.add_column('data_items', sa.Column('attributes', sa.UnicodeText()))
        for data_item in op.get_bind().execute(data_items.select().order_by(data_items.c.order)):
            attributes = {'values': {}}
            for attr in op.get_bind().execute(sa.select([data_set_attribute_keys.c.key, data_item_attributes.c.value]).select_from(data_item_attributes.join(data_set_attribute_keys, data_item_attributes.c.key_id == data_set_attribute_keys.c.id)).where(data_item_attributes.c.data_item_id == data_item[0])):
                if attr[0] == 'id_':
                    try:
                        parts = json.loads(attr[1])
                        if isinstance(parts, list):
                            child_ids = []
                            for idx, part in enumerate(parts):
                                if idx == 0:
                                    attributes['values'] = part
                                    child_ids.append(data_item[0])
                                else:
                                    child_ids.append(op.get_bind().execute(data_items.insert().values(order=data_item[1], control=data_item[2], dataset_id=data_item[3], attributes=json.dumps({'values': part}))).inserted_primary_key[0])
                            data_set = op.get_bind().execute(data_sets.select().where(data_sets.c.id == data_item[3])).first()
                            data_set_attr = json.loads(data_set[2])
                            data_set_attr['combinations'].append(child_ids)
                            op.get_bind().execute(data_sets.update().values(attributes=json.dumps(data_set_attr)).where(data_sets.c.id == data_item[3]))
                        else:
                            attributes['values'][attr[0]] = attr[1]
                    except:
                        attributes['values'][attr[0]] = attr[1]
                else:
                    attributes['values'][attr[0]] = attr[1]
            op.get_bind().execute(data_items.update().values(attributes=json.dumps(attributes)).where(data_items.c.id == data_item[0]))
    if 'owned_by' in [v['name'] for v in insp.get_columns('data_sets')]:
        op.drop_column('data_sets', 'owned_by')
    if 'data_set_item_attributes' in insp.get_table_names():
        op.drop_table('data_set_item_attributes')
    if 'data_item_attributes' in insp.get_table_names():
        op.drop_table('data_item_attributes')
    if 'data_set_attribute_keys' in insp.get_table_names():
        op.drop_table('data_set_attribute_keys')
    if 'data_set_relations' in insp.get_table_names():
        op.drop_table('data_set_relations')
    if 'data_item_control_answers' in insp.get_table_names():
        for control_answer in op.get_bind().execute(data_item_control_answers.select()):
            data_item = op.get_bind().execute(data_items.select().where(data_items.c.id == control_answer[1])).first()
            question = op.get_bind().execute(questions.select().where(questions.c.id == control_answer[2])).first()
            if data_item and question:
                attributes = json.loads(data_item[4])
                if 'answers' not in attributes:
                    attributes['answers'] = {}
                attributes['answers'][control_answer[2]] = control_answer[3]
                op.get_bind().execute(data_items.update().values(attributes=json.dumps(attributes)).where(data_items.c.id == control_answer[1]))
        op.drop_table('data_item_control_answers')
    if 'data_item_counts' in insp.get_table_names():
        op.drop_table('data_item_counts')
    # Participant migration
    if 'survey_id' in [v['name'] for v in insp.get_columns('participants')]:
        op.alter_column('participants', 'survey_id', new_column_name='experiment_id')
    if 'state' in [v['name'] for v in insp.get_columns('participants')]:
        op.drop_column('participants', 'state')
    if 'permutation_item_id' in [v['name'] for v in insp.get_columns('participants')]:
        op.drop_column('participants', 'permutation_item_id')
    if 'started' not in [v['name'] for v in insp.get_columns('participants')]:
        op.add_column('participants', sa.Column('started', sa.DateTime(), default=datetime.now))
        op.add_column('participants', sa.Column('updated', sa.DateTime(), default=datetime.now, onupdate=datetime.now))
        op.get_bind().execute(participants.update().values(started=datetime.now() - timedelta(hours=1), updated=datetime.now() - timedelta(hours=1)))
    if 'attributes' not in [v['name'] for v in insp.get_columns('participants')]:
        op.add_column('participants', sa.Column('attributes', sa.UnicodeText()))
    # Answers migration
    if 'attributes' not in [v['name'] for v in insp.get_columns('answers')]:
        op.add_column('answers', sa.Column('attributes', sa.UnicodeText()))
        for answer in op.get_bind().execute(answers.select()):
            response = None
            data_item_id = answer[3]
            for answer_value in op.get_bind().execute(answer_values.select().where(answer_values.c.answer_id == answer[0]).order_by(answer_values.c.id)):
                if answer_value[2]:
                    if '.' in answer_value[2]:
                        if response is None:
                            response = {}
                        try:
                            sub_did = int(answer_value[2].split('.')[0])
                            data_item = op.get_bind().execute(data_items.select().where(data_items.c.id == data_item_id)).first()
                            data_set = op.get_bind().execute(data_sets.select().where(data_sets.c.id == data_item[3])).first()
                            ds_attributes = json.loads(data_set[2])
                            for combination in ds_attributes['combinations']:
                                if data_item_id in combination:
                                    data_item_id = combination[sub_did]
                                    break
                            response[answer_value[2].split('.')[1]] = answer_value[3]
                        except Exception as e:
                            response[answer_value[2]] = answer_value[3]
                    else:
                        try:
                            sub_did = int(answer_value[2])
                            data_item = op.get_bind().execute(data_items.select().where(data_items.c.id == data_item_id)).first()
                            data_set = op.get_bind().execute(data_sets.select().where(data_sets.c.id == data_item[3])).first()
                            ds_attributes = json.loads(data_set[2])
                            for combination in ds_attributes['combinations']:
                                if data_item_id in combination:
                                    data_item_id = combination[sub_did]
                                    break
                            response = answer_value[3]
                        except Exception as e:
                            if response is None:
                                response = {}
                            response[answer_value[2]] = answer_value[3]
                else:
                    response = answer_value[3]
            attributes = {'response': response}
            op.get_bind().execute(answers.update().values(attributes=json.dumps(attributes), data_item_id=data_item_id).where(answers.c.id == answer[0]))
        op.drop_table('answer_values')


def downgrade():
    pass
