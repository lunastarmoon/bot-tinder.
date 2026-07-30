import os
import sqlite3
import threading

import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from http.server import HTTPServer, BaseHTTPRequestHandler

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

TOKEN = '8733102844:AAHtaPhcM5DhBo_SaAsXX8AbuiEXWWPt_RU'

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

DB_NAME = "tinder.db"

dados_cadastro = {}
dados_edicao = {}

# ==========================================================
# SERVIDOR HTTP (RENDER)
# ==========================================================

class ServidorHTTP(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot Tinder Online!")

def iniciar_servidor():

    porta = int(os.environ.get("PORT", 10000))

    servidor = HTTPServer(
        ("0.0.0.0", porta),
        ServidorHTTP
    )

    servidor.serve_forever()

threading.Thread(
    target=iniciar_servidor,
    daemon=True
).start()

# ==========================================================
# BANCO DE DADOS
# ==========================================================

def conectar():

    return sqlite3.connect(DB_NAME)

def iniciar_banco():

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfis(

            telegram_id INTEGER PRIMARY KEY,

            nome TEXT,

            idade INTEGER,

            bio TEXT,

            foto TEXT,

            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS curtidas(

            de_id INTEGER,

            para_id INTEGER,

            PRIMARY KEY(de_id, para_id)

        )
    """)

    conn.commit()
    conn.close()

iniciar_banco()

# ==========================================================
# TECLADOS
# ==========================================================

def teclado_menu():

    markup = InlineKeyboardMarkup(row_width=2)

    markup.add(
        InlineKeyboardButton(
            "❤️ Tinder",
            callback_data="menu_tinder"
        ),
        InlineKeyboardButton(
            "👤 Meu Perfil",
            callback_data="menu_perfil"
        )
    )

    markup.add(
        InlineKeyboardButton(
            "💌 Matches",
            callback_data="menu_matches"
        ),
        InlineKeyboardButton(
            "✏️ Editar Perfil",
            callback_data="menu_editar"
        )
    )

    markup.add(
        InlineKeyboardButton(
            "📝 Criar Perfil",
            callback_data="menu_cadastro"
        ),
        InlineKeyboardButton(
            "🗑 Excluir Perfil",
            callback_data="menu_deletar"
        )
    )

    markup.add(
        InlineKeyboardButton(
            "❓ Ajuda",
            callback_data="menu_ajuda"
        )
    )

    return markup

# ==========================================================
# MENU PRINCIPAL
# ==========================================================

def enviar_menu(chat_id):

    bot.send_message(

        chat_id,

        "🏠 *Menu Principal*\n\n"
        "Escolha uma opção abaixo.",

        reply_markup=teclado_menu()

    )

# ==========================================================
# START
# ==========================================================

@bot.message_handler(commands=["start"])
def start(message):

    texto = (
        "❤️ *Bem-vindo ao Tinder Bot!*\n\n"
        "Aqui você pode conhecer novas pessoas, "
        "curtir perfis e fazer matches.\n\n"
        "Para começar, crie seu perfil."
    )

    bot.send_message(

        message.chat.id,

        texto,

        reply_markup=teclado_menu()

    )

# ==========================================================
# AJUDA
# ==========================================================

@bot.message_handler(commands=["ajuda"])
def ajuda(message):

    texto = (
        "*📖 Comandos disponíveis*\n\n"

        "/start - Menu principal\n"

        "/cadastro - Criar perfil\n"

        "/perfil - Ver seu perfil\n"

        "/editar - Editar perfil\n"

        "/tinder - Ver pessoas\n"

        "/matches - Ver matches\n"

        "/deletar - Excluir perfil\n"

        "/ajuda - Mostrar ajuda"
    )

    bot.send_message(message.chat.id, texto)

# ==========================================================
# CALLBACK DO MENU
# ==========================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def callback_menu(call):

    bot.answer_callback_query(call.id)

    if call.data == "menu_cadastro":
        iniciar_cadastro(call.message)

    elif call.data == "menu_tinder":
        mostrar_proximo_perfil(call.message)

    elif call.data == "menu_perfil":
        ver_meu_perfil(call.message)

    elif call.data == "menu_editar":
        menu_editar(call.message)

    elif call.data == "menu_matches":
        ver_meus_matches(call.message)

    elif call.data == "menu_deletar":
        confirmar_saida(call.message)

    elif call.data == "menu_ajuda":
        ajuda(call.message)
        # ==========================================================
# CADASTRO
# ==========================================================

@bot.message_handler(commands=["cadastro"])
def iniciar_cadastro(message):

    user_id = message.chat.id

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT telegram_id FROM perfis WHERE telegram_id = ?",
        (user_id,)
    )

    existe = cursor.fetchone()
    conn.close()

    if existe:

        bot.send_message(
            user_id,
            "⚠️ Você já possui um perfil.\n\nUse /editar para alterá-lo."
        )
        return

    dados_cadastro[user_id] = {}

    msg = bot.send_message(
        user_id,
        "👤 Qual é o seu nome?"
    )

    bot.register_next_step_handler(msg, salvar_nome)


# ----------------------------------------------------------

def salvar_nome(message):

    user_id = message.chat.id

    if user_id not in dados_cadastro:
        return

    nome = message.text.strip()

    if len(nome) < 2:

        msg = bot.send_message(
            user_id,
            "❌ Digite um nome válido."
        )

        bot.register_next_step_handler(msg, salvar_nome)
        return

    dados_cadastro[user_id]["nome"] = nome

    msg = bot.send_message(
        user_id,
        "🎂 Qual é a sua idade?"
    )

    bot.register_next_step_handler(msg, salvar_idade)


# ----------------------------------------------------------

def salvar_idade(message):

    user_id = message.chat.id

    if user_id not in dados_cadastro:
        return

    try:

        idade = int(message.text)

    except ValueError:

        msg = bot.send_message(
            user_id,
            "❌ Digite apenas números."
        )

        bot.register_next_step_handler(msg, salvar_idade)
        return

    if idade < 19:

        bot.send_message(
            user_id,
            "🚫 Este bot é permitido apenas para maiores de 19 anos."
        )

        del dados_cadastro[user_id]
        return

    dados_cadastro[user_id]["idade"] = idade

    msg = bot.send_message(
        user_id,
        "📝 Escreva uma bio sobre você."
    )

    bot.register_next_step_handler(msg, salvar_bio)


# ----------------------------------------------------------

def salvar_bio(message):

    user_id = message.chat.id

    if user_id not in dados_cadastro:
        return

    bio = message.text.strip()

    if len(bio) < 5:

        msg = bot.send_message(
            user_id,
            "❌ Escreva uma bio um pouco maior."
        )

        bot.register_next_step_handler(msg, salvar_bio)
        return

    dados_cadastro[user_id]["bio"] = bio

    msg = bot.send_message(
        user_id,
        "📸 Agora envie sua foto de perfil."
    )

    bot.register_next_step_handler(msg, salvar_foto)


# ----------------------------------------------------------

def salvar_foto(message):

    user_id = message.chat.id

    if user_id not in dados_cadastro:
        return

    if message.content_type != "photo":

        msg = bot.send_message(
            user_id,
            "❌ Envie uma foto."
        )

        bot.register_next_step_handler(msg, salvar_foto)
        return

    foto = message.photo[-1].file_id

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO perfis(
            telegram_id,
            nome,
            idade,
            bio,
            foto
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        dados_cadastro[user_id]["nome"],
        dados_cadastro[user_id]["idade"],
        dados_cadastro[user_id]["bio"],
        foto
    ))

    conn.commit()
    conn.close()

    del dados_cadastro[user_id]

    bot.send_message(
        user_id,
        "✅ Perfil criado com sucesso!"
    )

    enviar_menu(user_id)
    # ==========================================================
# VER MEU PERFIL
# ==========================================================

@bot.message_handler(commands=["perfil"])
def ver_meu_perfil(message):

    user_id = message.chat.id

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nome, idade, bio, foto
        FROM perfis
        WHERE telegram_id = ?
    """, (user_id,))

    perfil = cursor.fetchone()

    conn.close()

    if not perfil:

        bot.send_message(
            user_id,
            "❌ Você ainda não possui um perfil.\n\nUse /cadastro."
        )
        return

    nome, idade, bio, foto = perfil

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM curtidas
        WHERE para_id = ?
    """, (user_id,))

    curtidas = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM curtidas c1
        WHERE c1.de_id = ?
        AND EXISTS(
            SELECT 1
            FROM curtidas c2
            WHERE c2.de_id = c1.para_id
            AND c2.para_id = ?
        )
    """, (user_id, user_id))

    matches = cursor.fetchone()[0]

    conn.close()

    markup = InlineKeyboardMarkup(row_width=2)

    markup.add(
        InlineKeyboardButton(
            "✏️ Editar Perfil",
            callback_data="menu_editar"
        ),
        InlineKeyboardButton(
            "🏠 Menu",
            callback_data="menu_inicio"
        )
    )

    legenda = (
        f"👤 *{nome}*\n"
        f"🎂 {idade} anos\n\n"
        f"📝 {bio}\n\n"
        f"❤️ Curtidas: {curtidas}\n"
        f"💌 Matches: {matches}"
    )

    bot.send_photo(
        user_id,
        foto,
        caption=legenda,
        reply_markup=markup
    )

# ==========================================================
# MENU EDITAR
# ==========================================================

@bot.message_handler(commands=["editar"])
def menu_editar(message):

    user_id = message.chat.id

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT telegram_id FROM perfis WHERE telegram_id=?",
        (user_id,)
    )

    if not cursor.fetchone():

        conn.close()

        bot.send_message(
            user_id,
            "❌ Você ainda não possui um perfil."
        )

        return

    conn.close()

    markup = InlineKeyboardMarkup(row_width=2)

    markup.add(
        InlineKeyboardButton(
            "👤 Nome",
            callback_data="editar_nome"
        ),
        InlineKeyboardButton(
            "🎂 Idade",
            callback_data="editar_idade"
        )
    )

    markup.add(
        InlineKeyboardButton(
            "📝 Bio",
            callback_data="editar_bio"
        ),
        InlineKeyboardButton(
            "📸 Foto",
            callback_data="editar_foto"
        )
    )

    markup.add(
        InlineKeyboardButton(
            "🏠 Menu",
            callback_data="menu_inicio"
        )
    )

    bot.send_message(
        user_id,
        "✏️ Escolha o que deseja editar:",
        reply_markup=markup
    )

# ==========================================================
# CALLBACK EDITAR
# ==========================================================

@bot.callback_query_handler(func=lambda c: c.data.startswith("editar_"))
def callback_editar(call):

    user_id = call.message.chat.id

    if call.data == "editar_nome":

        dados_edicao[user_id] = "nome"

        msg = bot.send_message(
            user_id,
            "👤 Digite o novo nome:"
        )

        bot.register_next_step_handler(
            msg,
            salvar_edicao
        )

    elif call.data == "editar_idade":

        dados_edicao[user_id] = "idade"

        msg = bot.send_message(
            user_id,
            "🎂 Digite a nova idade:"
        )

        bot.register_next_step_handler(
            msg,
            salvar_edicao
        )

    elif call.data == "editar_bio":

        dados_edicao[user_id] = "bio"

        msg = bot.send_message(
            user_id,
            "📝 Digite a nova bio:"
        )

        bot.register_next_step_handler(
            msg,
            salvar_edicao
        )

    elif call.data == "editar_foto":

        dados_edicao[user_id] = "foto"

        msg = bot.send_message(
            user_id,
            "📸 Envie a nova foto:"
        )

        bot.register_next_step_handler(
            msg,
            salvar_edicao_foto
        )

# ==========================================================
# SALVAR EDIÇÕES
# ==========================================================

def salvar_edicao(message):

    user_id = message.chat.id

    if user_id not in dados_edicao:
        return

    campo = dados_edicao[user_id]

    valor = message.text

    if campo == "idade":

        try:

            idade = int(valor)

        except:

            bot.send_message(
                user_id,
                "❌ Digite apenas números."
            )
            return

        if idade < 19:

            bot.send_message(
                user_id,
                "❌ A idade mínima é 19 anos."
            )
            return

        valor = idade

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        f"UPDATE perfis SET {campo}=? WHERE telegram_id=?",
        (valor, user_id)
    )

    conn.commit()
    conn.close()

    del dados_edicao[user_id]

    bot.send_message(
        user_id,
        "✅ Perfil atualizado com sucesso!"
    )

def salvar_edicao_foto(message):

    user_id = message.chat.id

    if user_id not in dados_edicao:
        return

    if message.content_type != "photo":

        bot.send_message(
            user_id,
            "❌ Envie uma foto."
        )
        return

    foto = message.photo[-1].file_id

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE perfis SET foto=? WHERE telegram_id=?",
        (foto, user_id)
    )

    conn.commit()
    conn.close()

    del dados_edicao[user_id]

    bot.send_message(
        user_id,
        "✅ Foto atualizada!"
)
