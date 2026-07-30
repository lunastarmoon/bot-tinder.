import os
import sqlite3
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- SERVIDOR HTTP FALSO PARA O RENDER ---
class ServidorFalso(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot Tinder rodando 24h!")

def rodar_servidor_falso():
    porta = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', porta), ServidorFalso)
    server.serve_forever()

threading.Thread(target=rodar_servidor_falso, daemon=True).start()

# --- CONEXÃO DO BOT TELEGRAM ---
API_TOKEN = '8733102844:AAEpegvJAW62cnAOeP-iphHSnKhCqe257dz4'
bot = telebot.TeleBot(API_TOKEN)
dados_cadastro = {}

# --- BANCO DE DADOS ATUALIZADO ---
def conectar_bd():
    return sqlite3.connect('tinder.db')

def iniciar_bd():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS perfis (
            telegram_id INTEGER PRIMARY KEY, 
            nome TEXT, 
            idade TEXT,
            bio TEXT, 
            foto TEXT,
            procura TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS curtidas (
            de_id INTEGER, para_id INTEGER, PRIMARY KEY (de_id, para_id)
        )
    ''')
    conn.commit()
    conn.close()

iniciar_bd()

# ----------------- FLUXO DE CADASTRO -----------------

@bot.message_handler(commands=['cadastro'])
def iniciar_cadastro(message):
    id_usuario = message.chat.id
    dados_cadastro[id_usuario] = {} 
    bot.send_message(id_usuario, "👋 Vamos criar o seu perfil!\n\nQual é o seu **Nome**?")
    bot.register_next_step_handler(message, salvar_nome)

def salvar_nome(message):
    id_usuario = message.chat.id
    if id_usuario not in dados_cadastro: return
    dados_cadastro[id_usuario]['nome'] = message.text
    bot.send_message(id_usuario, "E qual é a sua **Idade**?")
    bot.register_next_step_handler(message, salvar_idade)

def salvar_idade(message):
    id_usuario = message.chat.id
    if id_usuario not in dados_cadastro: return
    dados_cadastro[id_usuario]['idade'] = message.text
    
    # Pergunta o que procura (Amizade, Ficante, Namoro)
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Amizade 🤝", callback_data="proc_Amizade"),
        InlineKeyboardButton("Ficante 🔥", callback_data="proc_Ficante"),
        InlineKeyboardButton("Namoro ❤️", callback_data="proc_Namoro")
    )
    bot.send_message(id_usuario, "O que você está procurando no bot?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("proc_"))
def salvar_procura(call):
    id_usuario = call.message.chat.id
    if id_usuario not in dados_cadastro: return
    
    intencao = call.data.split("_")[1]
    dados_cadastro[id_usuario]['procura'] = intencao
    
    bot.edit_message_reply_markup(id_usuario, call.message.message_id, reply_markup=None)
    bot.send_message(id_usuario, "Ótimo! Agora digite uma **Bio** curta falando sobre você:")
    bot.register_next_step_handler(call.message, salvar_bio)

def salvar_bio(message):
    id_usuario = message.chat.id
    if id_usuario not in dados_cadastro: return
    dados_cadastro[id_usuario]['bio'] = message.text
    bot.send_message(id_usuario, "Por fim, envie uma **Foto de Perfil** bem bonita:")
    bot.register_next_step_handler(message, salvar_foto)

def salvar_foto(message):
    id_usuario = message.chat.id
    if id_usuario not in dados_cadastro: return
    if message.content_type == 'photo':
        id_foto = message.photo[-1].file_id
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO perfis (telegram_id, nome, idade, bio, foto, procura) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (id_usuario, dados_cadastro[id_usuario]['nome'], dados_cadastro[id_usuario]['idade'], dados_cadastro[id_usuario]['bio'], id_foto, dados_cadastro[id_usuario]['procura']))
        conn.commit()
        conn.close()
        bot.send_message(id_usuario, "🎉 Perfil criado com sucesso! Digite `/tinder` para começar a ver as pessoas.", parse_mode="Markdown")
        del dados_cadastro[id_usuario]
    else:
        bot.send_message(id_usuario, "❌ Por favor, envie uma foto válida.")
        bot.register_next_step_handler(message, salvar_foto)

# ----------------- ATUALIZAÇÃO PARCIAL DE PERFIL (EDITAR) -----------------

@bot.message_handler(commands=['editar'])
def menu_editar(message):
    my_id = message.chat.id
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM perfis WHERE telegram_id = ?", (my_id,))
    existe = cursor.fetchone()
    conn.close()

    if not existe:
        bot.send_message(my_id, "⚠️ Você precisa criar um perfil antes de editar! Use `/cadastro`.")
        return

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Mudar Idade 🎂", callback_data="edit_idade"),
        InlineKeyboardButton("Mudar Bio 📝", callback_data="edit_bio")
    )
    markup.row(
        InlineKeyboardButton("Mudar Foto 📸", callback_data="edit_foto"),
        InlineKeyboardButton("Mudar Objetivo 🎯", callback_data="edit_proc")
    )
    bot.send_message(my_id, "O que você deseja atualizar no seu perfil?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
def processar_edicao(call):
    my_id = call.message.chat.id
    bot.edit_message_reply_markup(my_id, call.message.message_id, reply_markup=None)
    
    if call.data == "edit_idade":
        bot.send_message(my_id, "Digite a sua **nova Idade**:")
        bot.register_next_step_handler(call.message, atualizar_idade_bd)
    elif call.data == "edit_bio":
        bot.send_message(my_id, "Digite a sua **nova Bio**:")
        bot.register_next_step_handler(call.message, atualizar_bio_bd)
    elif call.data == "edit_foto":
        bot.send_message(my_id, "Envie a sua **nova Foto de Perfil**:")
        bot.register_next_step_handler(call.message, atualizar_foto_bd)
    elif call.data == "edit_proc":
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("Amizade 🤝", callback_data="altproc_Amizade"),
            InlineKeyboardButton("Ficante 🔥", callback_data="altproc_Ficante"),
            InlineKeyboardButton("Namoro ❤️", callback_data="altproc_Namoro")
        )
        bot.send_message(my_id, "Escolha o seu novo objetivo:", reply_markup=markup)

def atualizar_idade_bd(message):
    my_id = message.chat.id
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("UPDATE perfis SET idade = ? WHERE telegram_id = ?", (message.text, my_id))
    conn.commit()
    conn.close()
    bot.send_message(my_id, "✅ Sua Idade foi atualizada com sucesso! Use `/perfil` para checar.")

def atualizar_bio_bd(message):
    my_id = message.chat.id
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("UPDATE perfis SET bio = ? WHERE telegram_id = ?", (message.text, my_id))
    conn.commit()
    conn.close()
    bot.send_message(my_id, "✅ Sua Bio foi atualizada com sucesso! Use `/perfil` para checar.")

def atualizar_foto_bd(message):
    my_id = message.chat.id
    if message.content_type == 'photo':
        id_foto = message.photo[-1].file_id
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("UPDATE perfis SET foto = ? WHERE telegram_id = ?", (id_foto, my_id))
        conn.commit()
        conn.close()
        bot.send_message(my_id, "✅ Sua Foto foi atualizada com sucesso!")
    else:
        bot.send_message(my_id, "❌ Envio inválido. Alteração cancelada.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("altproc_"))
def atualizar_procura_bd(call):
    my_id = call.message.chat.id
    nova_intencao = call.data.split("_")[1]
    bot.edit_message_reply_markup(my_id, call.message.message_id, reply_markup=None)
    
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("UPDATE perfis SET procura = ? WHERE telegram_id = ?", (nova_intencao, my_id))
    conn.commit()
    conn.close()
    bot.send_message(my_id, f"✅ Seu objetivo foi alterado para: **{nova_intencao}**!", parse_mode="Markdown")

# ----------------- VER SEU PERFIL -----------------

@bot.message_handler(commands=['perfil'])
def ver_meu_perfil(message):
    my_id = message.chat.id
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT nome, idade, bio, foto, procura FROM perfis WHERE telegram_id = ?", (my_id,))
    perfil = cursor.fetchone()
    conn.close()
    
    if perfil:
        nome, idade, bio, foto, procura = perfil
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("⚙️ Editar Informações", callback_data="edit_menu_rapido"))
        bot.send_photo(
            my_id, foto, 
            caption=f"📝 **Seu Perfil Atual:**\n\n**Nome:** {nome}\n**Idade:** {idade} anos\n**Procura por:** {procura}\n**Bio:** {bio}\n\nUse `/editar` para mudar dados avulsos.",
            reply_markup=markup, parse_mode="Markdown"
        )
    else:
        bot.send_message(my_id, "⚠️ Você ainda não tem um perfil criado! Digite `/cadastro`.")

@bot.callback_query_handler(func=lambda call: call.data == "edit_menu_rapido")
def redirecionar_edicao(call):
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    menu_editar(call.message)

# ----------------- VER MATCHS -----------------

@bot.message_handler(commands=['matches', 'matchs'])
def ver_meus_matches(message):
    my_id = message.chat.id
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.nome, p.telegram_id FROM perfis p
        WHERE p.telegram_id IN (SELECT para_id FROM curtidas WHERE de_id = ?) 
match_existe = cursor.fetchone()cursor.execute("SELECT nome FROM perfis WHERE telegram_id = ?", (my_id,))resultado_nome = cursor.fetchone()meu_nome = resultado_nome[0] if resultado_nome else "Alguém"conn.close()bot.edit_message_reply_markup(my_id, call.message.message_id, reply_markup=None)if match_existe:bot.answer_callback_query(call.id, "É UM MATCH! 😍", show_alert=True)bot.send_message(my_id, "🎉 MATCH! Vocês se curtiram mutuamente! Use /matches para conversar.")try:bot.send_message(alvo_id, f"🎉 MATCH! O perfil {meu_nome} te curtiu de volta! Use /matches para conversar.")except Exception: passelse:bot.answer_callback_query(call.id, "Você curtiu o perfil!")mostrar_proximo_perfil(call.message)elif call.data.startswith("prox_"):bot.edit_message_reply_markup(my_id, call.message.message_id, reply_markup=None)bot.answer_callback_query(call.id, "Próximo...")mostrar_proximo_perfil(call.message)@bot.message_handler(commands=['sair', 'deletar'])def confirmar_saida(message):id_usuario = message.chat.idmarkup = InlineKeyboardMarkup()markup.row(InlineKeyboardButton("✅ Sim, apagar tudo", callback_data="confirmar_deletar"), InlineKeyboardButton("❌ Não, continuar", callback_data="cancelar_deletar"))bot.send_message(id_usuario, "⚠️ Tem certeza que deseja apagar seu perfil?", reply_markup=markup)bot.infinity_polling()
