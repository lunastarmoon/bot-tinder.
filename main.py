import os
import time
import threading

import telebot
import psycopg2

from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from http.server import HTTPServer, BaseHTTPRequestHandler

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise Exception("TOKEN não encontrado nas variáveis de ambiente.")

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

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

    porta = int(os.environ.get("PORT", 5000))

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
    return psycopg2.connect(os.getenv("DATABASE_URL"))


def iniciar_banco():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfis(

            telegram_id BIGINT PRIMARY KEY,

            nome TEXT NOT NULL,

            idade INTEGER NOT NULL,

            bio TEXT,

            foto TEXT,

            username TEXT,

            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS curtidas(

            de_id BIGINT,

            para_id BIGINT,

            PRIMARY KEY(de_id, para_id)

        )
    """)

    conn.commit()
    conn.close()


iniciar_banco()

# ==========================================================
# MENU
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
            "✏️ Editar",
            callback_data="menu_editar"
        )
    )

    markup.add(
        InlineKeyboardButton(
            "📊 Estatísticas",
            callback_data="menu_stats"
        ),
        InlineKeyboardButton(
            "🗑️ Excluir",
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


def enviar_menu(chat_id):

    texto = (
        "🏠 *Menu Principal*\n\n"
        "Escolha uma opção abaixo."
    )

    bot.send_message(
        chat_id,
        texto,
        reply_markup=teclado_menu()
    )

# ==========================================================
# START
# ==========================================================

@bot.message_handler(commands=["start"])
def start(message):

    texto = (
        "❤️ *Bem-vindo ao Tinder RP!*\n\n"
        "Crie seu perfil, conheça pessoas, curta perfis e faça matches.\n\n"
        "Use o menu abaixo para começar."
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
        "/cadastro\n"
        "/perfil\n"
        "/editar\n"
        "/tinder\n"
        "/matches\n"
        "/stats\n"
        "/deletar\n"
        "/cancelar"
    )

    bot.send_message(
        message.chat.id,
        texto
)

# ==========================================================
# CALLBACKS DO MENU
# ==========================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def botoes_menu(call):

    bot.answer_callback_query(call.id)

    if call.data == "menu_tinder":
        mostrar_proximo_perfil(call.message)

    elif call.data == "menu_perfil":
        ver_meu_perfil(call.message)

    elif call.data == "menu_matches":
        ver_meus_matches(call.message)

    elif call.data == "menu_editar":
        menu_editar(call.message)

    elif call.data == "menu_stats":
        estatisticas_perfil(call.message)

    elif call.data == "menu_deletar":
        confirmar_deletar(call.message)

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
        "SELECT telegram_id FROM perfis WHERE telegram_id=%s",
        (user_id,)
    )

    if cursor.fetchone():

        conn.close()

        bot.send_message(
            user_id,
            "⚠️ Você já possui um perfil.\nUse /editar para alterá-lo."
        )
        return

    conn.close()

    dados_cadastro[user_id] = {}

    msg = bot.send_message(
        user_id,
        "👤 Qual é o seu nome?"
    )

    bot.register_next_step_handler(msg, salvar_nome)


def salvar_nome(message):

    user_id = message.chat.id

    if user_id not in dados_cadastro:
        return

    nome = message.text.strip()

    if len(nome) < 

    # ==========================================================
# SALVAR FOTO
# ==========================================================

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

    try:

        cursor.execute("""
            INSERT INTO perfis (
                telegram_id,
                nome,
                idade,
                bio,
                foto,
                username
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            dados_cadastro[user_id]["nome"],
            dados_cadastro[user_id]["idade"],
            dados_cadastro[user_id]["bio"],
            foto,
            dados_cadastro[user_id]["username"]
        ))

        conn.commit()

        bot.send_message(
            user_id,
            "✅ Perfil criado com sucesso!"
        )

        enviar_menu(user_id)

        del dados_cadastro[user_id]

    except Exception as erro:

        bot.send_message(
            user_id,
            f"❌ Erro ao salvar perfil:\n{erro}"
        )

    finally:

        conn.close()


# ==========================================================
# VER PERFIL
# ==========================================================

@bot.message_handler(commands=["perfil"])
def ver_meu_perfil(message):

    user_id = message.chat.id

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nome, idade, bio, foto
        FROM perfis
        WHERE telegram_id=%s
    """, (user_id,))

    perfil = cursor.fetchone()

    if not perfil:

        conn.close()

        bot.send_message(
            user_id,
            "❌ Você ainda não possui um perfil."
        )

        return

    nome, idade, bio, foto = perfil

    cursor.execute("""
        SELECT COUNT(*)
        FROM curtidas
        WHERE para_id=%s
    """, (user_id,))

    curtidas = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM curtidas c1
        WHERE c1.de_id=%s
        AND EXISTS(
            SELECT 1
            FROM curtidas c2
            WHERE c2.de_id=c1.para_id
            AND c2.para_id=%s
        )
    """, (user_id, user_id))

    matches = cursor.fetchone()[0]

    conn.close()

    legenda = (
        f"👤 *{nome}*\n"
        f"🎂 {idade} anos\n\n"
        f"📝 {bio}\n\n"
        f"❤️ Curtidas: {curtidas}\n"
        f"💌 Matches: {matches}"
    )

    markup = InlineKeyboardMarkup(row_width=2)

    markup.add(
        InlineKeyboardButton(
            "✏️ Editar",
            callback_data="menu_editar"
        ),
        InlineKeyboardButton(
            "🏠 Menu",
            callback_data="menu_inicio"
        )
    )

    bot.send_photo(
        user_id,
        foto,
        caption=legenda,
        reply_markup=markup
    )


# ==========================================================
# MATCHES
# ==========================================================

@bot.message_handler(commands=["matches"])
def ver_meus_matches(message):

    user_id = message.chat.id

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.nome, p.username
        FROM perfis p
        WHERE p.telegram_id IN (
            SELECT para_id
            FROM curtidas
            WHERE de_id=%s
        )
        AND p.telegram_id IN (
            SELECT de_id
            FROM curtidas
            WHERE para_id=%s
        )
    """, (user_id, user_id))

    matches = cursor.fetchall()

    conn.close()

    if not matches:

        bot.send_message(
            user_id,
            "💔 Você ainda não possui matches."
        )

        return

    texto = "💌 *Seus Matches*\n\n"

    for nome, username in matches:

        if username:
            username = username.replace("@", "")
            texto += f"❤️ {nome} (@{username})\n"
        else:
            texto += f"❤️ {nome}\n"

    bot.send_message(
        user_id,
        texto
    )

