import os
import json

class Generator:
    def __init__(self):
        self.commands = []
        self.bot_token = "process.env.DISCORD_TOKEN"

    def generate(self, node):
        body_nodes = node.body if hasattr(node, 'body') else (node.statements if hasattr(node, 'statements') else [])
        
        command_handlers = []
        button_handlers = []
        command_list = []

        # First pass: collect all commands for gateway registration
        for child in body_nodes:
            ntype = child.__class__.__name__
            if ntype in ['CommandNode', 'CommandBlockNode']:
                cmd_name = getattr(child, 'name', getattr(child, 'command_name', None))
                if cmd_name:
                    command_list.append(f"{{ name: '{cmd_name}', description: 'Command /{cmd_name}' }}")

        cmd_metas_str = ",\n        ".join(command_list)

        # Base Boilerplate split safely to prevent Python f-string curly brace collisions
        js_code = (
            "const { Client, GatewayIntentBits, REST, Routes, ActionRowBuilder, ButtonBuilder, ButtonStyle, EmbedBuilder, PermissionFlagsBits, MessageFlags } = require('discord.js');\n"
            "const fs = require('fs');\n"
            "const path = require('path');\n\n"
            "const dbFile = path.join(__dirname, 'dbot_database.json');\n"
            "const db = {\n"
            "    set(key, value) {\n"
            "        let data = {};\n"
            "        if (fs.existsSync(dbFile)) data = JSON.parse(fs.readFileSync(dbFile));\n"
            "        data[key] = value;\n"
            "        fs.writeFileSync(dbFile, JSON.stringify(data, null, 2));\n"
            "    },\n"
            "    get(key) {\n"
            "        if (!fs.existsSync(dbFile)) return null;\n"
            "        let data = JSON.parse(fs.readFileSync(dbFile));\n"
            "        return data[key] !== undefined ? data[key] : null;\n"
            "    }\n"
            "};\n\n"
            "const client = new Client({\n"
            "    intents: [\n"
            "        GatewayIntentBits.Guilds,\n"
            "        GatewayIntentBits.GuildMessages,\n"
            "        GatewayIntentBits.MessageContent\n"
            "    ]\n"
            "});\n\n"
            "client.once('clientReady', async () => {\n"
            "    console.log('Logged in as ' + client.user.tag + '!');\n"
            "    const commands = [\n"
            f"        {cmd_metas_str}\n"
            "    ];\n\n"
            f"    const rest = new REST({{ version: '10' }}).setToken({self.bot_token});\n"
            "    try {\n"
            "        console.log('Registering application (/) commands...');\n"
            "        await rest.put(\n"
            "            Routes.applicationCommands(client.user.id),\n"
            "            { body: commands },\n"
            "        );\n"
            "        console.log('Successfully registered commands!');\n"
            "    } catch (error) {\n"
            "        console.error('Error registering commands:', error);\n"
            "    }\n"
            "});\n"
        )

        # Second pass: generate interaction event handlers
        for child in body_nodes:
            ntype = child.__class__.__name__
            
            if ntype in ['CommandNode', 'CommandBlockNode']:
                cmd_name = getattr(child, 'name', getattr(child, 'command_name', None))
                modifiers = getattr(child, 'modifiers', [])
                is_admin = getattr(child, 'is_admin', False) or 'admin' in modifiers
                
                inner_js = ""
                if is_admin:
                    inner_js += '        if (!interaction.member.permissions.has(PermissionFlagsBits.Administrator)) {\n'
                    inner_js += '            return interaction.reply({ content: "You do not have permissions to use this command", flags: MessageFlags.Ephemeral });\n'
                    inner_js += '        }\n'
                
                body = getattr(child, 'body', [])
                inner_js += self.generate_statements(body, depth=8)
                
                handler = f"    if (interaction.isChatInputCommand() && interaction.commandName === '{cmd_name}') {{\n{inner_js}        return;\n    }}"
                command_handlers.append(handler)
                
            elif ntype in ['OnButtonNode', 'ButtonClickBlockNode']:
                btn_id = getattr(child, 'button_id', getattr(child, 'custom_id', None))
                body = getattr(child, 'body', [])
                inner_js = self.generate_statements(body, depth=8)
                handler = f"    if (interaction.isButton() && interaction.customId === '{btn_id}') {{\n{inner_js}        return;\n    }}"
                button_handlers.append(handler)

        js_code += "\nclient.on('interactionCreate', async interaction => {\n"
        for ch in command_handlers:
            js_code += ch + "\n\n"
        for bh in button_handlers:
            js_code += bh + "\n\n"
        js_code += "});\n\n"
        
        js_code += f"client.login({self.bot_token});\n"
        return js_code

    def generate_statements(self, statements, depth):
        indent = " " * depth
        lines = []
        
        for idx, stmt in enumerate(statements):
            stype = stmt.__class__.__name__
            
            if stype in ['LetDeclarationNode', 'AssignmentNode']:
                name = getattr(stmt, 'name', None)
                if not name and hasattr(stmt, 'target'):
                    name = ".".join(stmt.target.path) if hasattr(stmt.target, 'path') else str(stmt.target)
                
                raw_val = getattr(stmt, 'value', "")
                val = "string"
                if hasattr(raw_val, 'value'):
                    val = json.dumps(raw_val.value)
                elif hasattr(raw_val, 'path'):
                    path = raw_val.path
                    if path == ["user", "name"] or path == ["player", "name"]: val = "interaction.user.username"
                    elif path == ["message", "content"]: val = "interaction.message.content"
                    else: val = ".".join(path)
                else:
                    val = str(raw_val)
                    if val == "user.name" or val == "player.name": val = "interaction.user.username"
                    elif val == "message.content": val = "interaction.message.content"

                lines.append(f"{indent}let {name} = {val};")
                
            elif stype in ['ReplyNode', 'AnswerNode', 'SendMsgNode']:
                raw_msg = getattr(stmt, 'message', getattr(stmt, 'text', ""))
                text = json.dumps(raw_msg.value) if hasattr(raw_msg, 'value') else str(raw_msg)
                
                # Check if your parser flagged this statement as ephemeral/private
                is_ephemeral = (
                    getattr(stmt, 'is_private', False) or 
                    getattr(stmt, 'ephemeral', False) or 
                    getattr(stmt, 'hidden', False) or
                    'private' in getattr(stmt, 'modifiers', []) or
                    'hidden' in getattr(stmt, 'modifiers', [])
                )
                flags_str = ", flags: MessageFlags.Ephemeral" if is_ephemeral else ""
                
                buttons = getattr(stmt, 'buttons', [])
                
                if buttons:
                    lines.append(f"{indent}const row = new ActionRowBuilder().addComponents([")
                    for b_idx, btn in enumerate(buttons):
                        btn_label = getattr(btn, 'label', '')
                        if hasattr(btn_label, 'value'): btn_label = btn_label.value
                        btn_id = getattr(btn, 'button_id', getattr(btn, 'custom_id', ''))
                        if hasattr(btn_id, 'value'): btn_id = btn_id.value
                        btn_style = getattr(btn, 'style', 'green')
                        
                        style_map = {"green": "ButtonStyle.Success", "blue": "ButtonStyle.Primary", "red": "ButtonStyle.Danger", "grey": "ButtonStyle.Secondary"}
                        b_style = style_map.get(str(btn_style).lower(), "ButtonStyle.Primary")
                        
                        comma = "," if b_idx < len(buttons) - 1 else ""
                        lines.append(f"{indent}    new ButtonBuilder().setCustomId('{btn_id}').setLabel('{btn_label}').setStyle({b_style}){comma}")
                    lines.append(f"{indent}]);")
                    lines.append(f"{indent}await interaction.reply({{ content: {text}, components: [row]{flags_str} }});")
                else:
                    lines.append(f"{indent}await interaction.reply({{ content: {text}{flags_str} }});")
                    
            elif stype in ['CreateChannelNode', 'CreateChannelBlockNode']:
                c_name = "interaction.user.username"
                is_p = "false"
                allowed_users_expr = "[]"
                props = getattr(stmt, 'properties', {})
                
                def unpack_val(val_node):
                    if hasattr(val_node, 'value'): return json.dumps(val_node.value)
                    elif hasattr(val_node, 'path'):
                        path = val_node.path
                        if path == ["user", "name"] or path == ["player", "name"]: return "interaction.user.username"
                        return ".".join(path)
                    return "interaction.user.username"

                def unpack_raw_val(val_node):
                    if hasattr(val_node, 'path'): return ".".join(val_node.path)
                    if hasattr(val_node, 'value'): return str(val_node.value)
                    return str(val_node)

                if isinstance(props, list):
                    for prop in props:
                        p_name = getattr(prop, 'name', '')
                        p_val = getattr(prop, 'value', None)
                        if p_name == 'name': c_name = unpack_val(p_val)
                        if p_name == 'private': is_p = "true" if getattr(p_val, 'value', p_val) else "false"
                        if p_name in ['allow', 'users', 'players']: allowed_users_expr = unpack_raw_val(p_val)
                elif isinstance(props, dict):
                    if "name" in props: c_name = unpack_val(props["name"])
                    if "private" in props or "isPrivate" in props: is_p = "true"
                    for k in ['allow', 'users', 'players']:
                        if k in props: allowed_users_expr = unpack_raw_val(props[k])

                lines.append(f"{indent}await interaction.guild.channels.create({{")
                lines.append(f"{indent}    name: {c_name},")
                lines.append(f"{indent}    type: 0,")
                if is_p == "true":
                    lines.append(f"{indent}    permissionOverwrites: [")
                    lines.append(f"{indent}        {{ id: interaction.guild.id, deny: [PermissionFlagsBits.ViewChannel] }},")
                    lines.append(f"{indent}        {{ id: interaction.user.id, allow: [PermissionFlagsBits.ViewChannel] }},")
                    # 🔥 Fixed: Uses standard JS short-circuit typeof checking so missing/undeclared list bindings default gracefully to [] instead of crashing!
                    lines.append(f"{indent}        ...((typeof {allowed_users_expr} !== 'undefined' && Array.isArray({allowed_users_expr})) ? {allowed_users_expr} : []).map(u => ({{ id: typeof u === 'string' ? u : (u.id || u), allow: [PermissionFlagsBits.ViewChannel] }}))")
                    lines.append(f"{indent}    ]")
                lines.append(f"{indent}}});")
                
            elif stype in ['PassthroughNode', 'RawJsNode', 'RawJSNode']:
                expr_text = getattr(stmt, 'expr', getattr(stmt, 'code', ""))
                lines.append(f"{indent}{expr_text.replace('$', '')}")
                
        return "\n".join(lines) + "\n"

    def transpile(self, ast):
        return self.generate(ast)
