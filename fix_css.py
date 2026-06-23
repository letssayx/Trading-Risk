import re

with open('backend/ui/templates/chat.html', 'r') as f:
    chat_html = f.read()

# Make sure CSS exists for dropdown
if "custom-dropdown" not in chat_html[:chat_html.find('</style>')]:
    css_to_add = '''
        /* Custom Checkbox Dropdowns */
        .custom-dropdown { position: relative; display: inline-block; }
        .dropdown-toggle {
            padding: 8px; border-radius: 4px; border: 1px solid #444; background: #222; color: #fff; cursor: pointer; user-select: none;
            display: flex; align-items: center; justify-content: space-between; width: 140px; box-sizing: border-box;
        }
        .dropdown-toggle::after { content: '▼'; font-size: 10px; margin-left: 8px; }
        .dropdown-menu {
            display: none; position: absolute; background-color: #333; min-width: 140px;
            box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.5); z-index: 1000;
            border: 1px solid #555; border-radius: 4px; max-height: 250px; overflow-y: auto; top: 100%; left: 0;
        }
        .dropdown-menu label {
            display: block; padding: 6px 12px; cursor: pointer; color: white; margin: 0; font-size: 13px;
        }
        .dropdown-menu label:hover { background-color: #444; }
        .dropdown-menu input[type="checkbox"] { margin-right: 8px; cursor: pointer; }
        .custom-dropdown.open .dropdown-menu { display: block; }
        .custom-dropdown.open .dropdown-toggle { border-color: #666; background: #2a2a2a; }
'''
    chat_html = chat_html.replace('    </style>', css_to_add + '\n    </style>')

with open('backend/ui/templates/chat.html', 'w') as f:
    f.write(chat_html)
