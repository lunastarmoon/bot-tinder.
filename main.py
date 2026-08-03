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

# ==========================================================
# EDITAR PERFIL
# ==========================================================

@bot.message_handler(commands=["editar"])
def menu_editar(message):

    user_id = message.chat.id

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT telegram_id FROM perfis WHERE telegram_id=%s",
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
        InlineKeyboardButton("👤 Nome", callback_data="editar_nome"),
        InlineKeyboardButton("🎂 Idade", callback_data="editar_idade")
    )

    markup.add(
        InlineKeyboardButton("📝 Bio", callback_data="editar_bio"),
        InlineKeyboardButton("📸 Foto", callback_data="editar_foto")
    )

    markup.add(
        InlineKeyboardButton("🏠 Menu", callback_data="menu_inicio")
    )

    bot.send_message(
        user_id,
        "✏️ O que deseja editar?",
        reply_markup=markup
    )


# ==========================================================
# CALLBACK EDITAR
# ==========================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("editar_"))
def callback_editar(call):

    user_id = call.message.chat.id

    if call.data == "editar_nome":
        dados_edicao[user_id] = "nome"
        msg = bot.send_message(user_id, "Digite o novo nome:")
        bot.register_next_step_handler(msg, salvar_edicao)

    elif call.data == "editar_idade":
        dados_edicao[user_id] = "idade"
        msg = bot.send_message(user_id, "Digite a nova idade:")
        bot.register_next_step_handler(msg, salvar_edicao)

    elif call.data == "editar_bio":
        dados_edicao[user_id] = "bio"
        msg = bot.send_message(user_id, "Digite a nova bio:")
        bot.register_next_step_handler(msg, salvar_edicao)

    elif call.data == "editar_foto":
        dados_edicao[user_id] = "foto"
        msg = bot.send_message(user_id, "Envie a nova foto:")
        bot.register_next_step_handler(msg, salvar_edicao_foto)


def salvar_edicao(message):

    user_id = message.chat.id

    if user_id not in dados_edicao:
        return

    campo = dados_edicao[user_id]
    valor = message.text.strip()

    if campo == "idade":

        try:
            valor = int(valor)
        except:
            bot.send_message(user_id, "Digite apenas números.")
            return

        if valor < 18:
            bot.send_message(user_id, "A idade mínima é 18 anos.")
            return

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        f"UPDATE perfis SET {campo}=%s WHERE telegram_id=%s",
        (valor, user_id)
    )

    conn.commit()
    conn.close()

    del dados_edicao[user_id]

    bot.send_message(
        user_id,
        "✅ Perfil atualizado!"
    )


def salvar_edicao_foto(message):

    user_id = message.chat.id

    if user_id not in dados_edicao:
        return

    if message.content_type != "photo":
        bot.send_message(user_id, "Envie uma foto.")
        return

    foto = message.photo[-1].file_id

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE perfis SET foto=%s WHERE telegram_id=%s",
        (foto, user_id)
    )

    conn.commit()
    conn.close()

    del dados_edicao[user_id]

    bot.send_message(
        user_id,
        "✅ Foto atualizada!"
    )

# ==========================================================
# TINDER
# ==========================================================

@bot.message_handler(commands=["tinder"])
def mostrar_proximo_perfil(message):

    user_id = message.chat.id

    conn = conectar()
    cursor = conn.cursor()

    # Verifica se possui perfil
    cursor.execute(
        "SELECT telegram_id FROM perfis WHERE telegram_id=%s",
        (user_id,)
    )

    if not cursor.fetchone():

        conn.close()

        bot.send_message(
            user_id,
            "❌ Você precisa criar um perfil primeiro.\n\nUse /cadastro."
        )

        return

    # Busca um perfil ainda não visto
    cursor.execute("""
        SELECT
            telegram_id,
            nome,
            idade,
            bio,
            foto
        FROM perfis
        WHERE telegram_id <> %s
        AND telegram_id NOT IN(
            SELECT para_id
            FROM curtidas
            WHERE de_id=%s
        )
        ORDER BY RANDOM()
        LIMIT 1
    """, (user_id, user_id))

    perfil = cursor.fetchone()

    conn.close()

    if not perfil:

        bot.send_message(
            user_id,
            "✨ Você já viu todos os perfis disponíveis."
        )

        return

    perfil_id, nome, idade, bio, foto = perfil

    markup = InlineKeyboardMarkup(row_width=2)

    markup.add(
        InlineKeyboardButton(
            "❌ Pular",
            callback_data=f"nao_{perfil_id}"
        ),
        InlineKeyboardButton(
            "❤️ Curtir",
            callback_data=f"sim_{perfil_id}"
        )
    )

    markup.add(
        InlineKeyboardButton(
            "🏠

    # ==========================================================
# ESTATÍSTICAS
# ==========================================================

@bot.message_handler(commands=["stats"])
def estatisticas_perfil(message):

    user_id = message.chat.id

    conn = conectar()
    cursor = conn.cursor()

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

    texto = (
        "📊 *Suas Estatísticas*\n\n"
        f"❤️ Curtidas recebidas: {curtidas}\n"
        f"💌 Matches: {matches}"
    )

    markup = InlineKeyboardMarkup()

    markup.add(
        InlineKeyboardButton(
            "🏠 Menu",
            callback_data="menu_inicio"
        )
    )

    bot.send_message(
        user_id,
        texto,
        reply_markup=markup
    )


# ==========================================================
# EXCLUIR PERFIL
# ==========================================================

@bot.message_handler(commands=["deletar"])
def confirmar_deletar(message):

    user_id = message.chat.id

    markup = InlineKeyboardMarkup(row_width=2)

    markup.add(
        InlineKeyboardButton(
            "✅ Sim",
            callback_data="confirma_deleta"
        ),
        InlineKeyboardButton(
            "❌ Cancelar",
            callback_data="cancela_deleta"
        )
    )

    bot.send_message(
        user_id,
        "⚠️ Tem certeza que deseja apagar seu perfil?\n\nEssa ação não pode ser desfeita.",
        reply_markup=markup
    )


# ==========================================================
# CALLBACK EXCLUIR
# ==========================================================

@bot.callback_query_handler(
    func=lambda call: call.data in [
        "confirma_deleta",
        "cancela_deleta"
    ]
)
def callback_deletar(call):

    user_id = call.message.chat.id

    bot.answer_callback_query(call.id)

    if call.data == "confirma_deleta":

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM perfis WHERE telegram_id=%s",
            (user_id,)
        )

        cursor.execute(
            """
            DELETE FROM curtidas
            WHERE de_id=%s
            OR para_id=%s
            """,
            (user_id, user_id)
        )

        conn.commit()
        conn.close()

        bot.send_message(
            user_id,
            "🗑️ Perfil excluído com sucesso."
        )

    else:

        bot.send_message(
            user_id,
            "❌ Operação cancelada."
        )

    try:
        bot.delete_message(
            user_id,
            call.message.message_id
        )
    except:
        pass

    enviar_menu(user_id)


# ==========================================================
# CANCELAR
# ==========================================================

@bot.message_handler(commands=["cancelar"])
def cancelar_operacao(message):

    user_id = message.chat.id

    if user_id in dados_cadastro:
        del dados_cadastro[user_id]

    if user_id in dados_edicao:
        del dados_edicao[user_id]

    bot.send_message(
        user_id,
        "❌ Operação cancelada.",
        reply_markup=teclado_menu()
    )


@bot.callback_query_handler(func=lambda call: call.data == "cancelar")
def cancelar_botao(call):

    user_id = call.message.chat.id

    if user_id in dados_cadastro:
        del dados

