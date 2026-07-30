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
    server = HTTPServer(("0.0.0.0", porta), ServidorFalso)
    server.serve_forever()

threading.Thread(target=rodar_servidor_falso, daemon=True).start()

# --- CONEXÃO DO BOT TELEGRAM ---
API_TOKEN ='8733102844:AAEghsGpIFHS-DwJOVj-dajo6sYUIA7DjF0'
bot = telebot.TeleBot(API_TOKEN)

dados_cadastro = {}

# ----------------- BANCO DE DADOS -----------------

def conectar_bd():
    return sqlite3.connect("tinder.db")

def iniciar_bd():
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfis (
            telegram_id INTEGER PRIMARY KEY,
            nome TEXT,
            idade TEXT,
            bio TEXT,
            foto TEXT,
            procura TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS curtidas (
            de_id INTEGER,
            para_id INTEGER,
            PRIMARY KEY (de_id, para_id)
        )
    """)

    conn.commit()
    conn.close()

iniciar_bd()

# ----------------- CADASTRO -----------------

@bot.message_handler(commands=["cadastro"])
def iniciar_cadastro(message):
    user_id = message.chat.id
    dados_cadastro[user_id] = {}

    bot.send_message(user_id, "Qual é o seu **Nome**?")
    bot.register_next_step_handler(message, salvar_nome)

def salvar_nome(message):
    user_id = message.chat.id

    if user_id not in dados_cadastro:
        return

    dados_cadastro[user_id]["nome"] = message.text

    bot.send_message(user_id, "Qual é a sua **Idade**?")
    bot.register_next_step_handler(message, salvar_idade)

def salvar_idade(message):
    user_id = message.chat.id

    if user_id not in dados_cadastro:
        return

    dados_cadastro[user_id]["idade"] = message.text

    markup = InlineKeyboardMarkup()

    markup.row(
        InlineKeyboardButton("Amizade 🤝", callback_data="proc_Amizade"),
        InlineKeyboardButton("Ficante 🔥", callback_data="proc_Ficante"),
        InlineKeyboardButton("Namoro ❤️", callback_data="proc_Namoro"),
    )

    bot.send_message(
        user_id,
        "O que você procura?",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("proc_"))
def salvar_procura(call):
    user_id = call.message.chat.id

    if user_id not in dados_cadastro:
        return

    dados_cadastro[user_id]["procura"] = call.data.split("_")[1]

    bot.edit_message_reply_markup(
        user_id,
        call.message.message_id,
        reply_markup=None
    )

    bot.send_message(user_id, "Digite sua **Bio**:")

    bot.register_next_step_handler(call.message, salvar_bio)

def salvar_bio(message):
    user_id = message.chat.id

    if user_id not in dados_cadastro:
        return

    dados_cadastro[user_id]["bio"] = message.text

    bot.send_message(user_id, "Agora envie sua **foto de perfil**.")

    bot.register_next_step_handler(message, salvar_foto)

def salvar_foto(message):
    user_id = message.chat.id

    if user_id not in dados_cadastro:
        return

    if message.content_type != "photo":
        bot.send_message(user_id, "❌ Envie uma foto válida.")
        bot.register_next_step_handler(message, salvar_foto)
        return

    foto = message.photo[-1].file_id

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO perfis
        (telegram_id, nome, idade, bio, foto, procura)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        dados_cadastro[user_id]["nome"],
        dados_cadastro[user_id]["idade"],
        dados_cadastro[user_id]["bio"],
        foto,
        dados_cadastro[user_id]["procura"]
    ))

    conn.commit()
    conn.close()

    del dados_cadastro[user_id]

    bot.send_message(
        user_id,
        "🎉 Perfil criado! Use /tinder."
    )

# ----------------- EDITAR PERFIL -----------------

@bot.message_handler(commands=["editar"])
def menu_editar(message):
    user_id = message.chat.id

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM perfis WHERE telegram_id=?",
        (user_id,)
    )

    existe = cursor.fetchone()

    conn.close()

    if not existe:
        bot.send_message(
            user_id,
            "Crie um perfil primeiro usando /cadastro."
        )
        return

    markup = InlineKeyboardMarkup()

    markup.row(
        InlineKeyboardButton("Idade 🎂", callback_data="edit_idade"),
        InlineKeyboardButton("Bio 📝", callback_data="edit_bio")
    )

    markup.row(
        InlineKeyboardButton("Foto 📸", callback_data="edit_foto"),
        InlineKeyboardButton("Objetivo 🎯", callback_data="edit_proc")
    )

    bot.send_message(
        user_id,
        "Escolha o que deseja editar:",
        reply_markup=markup
    )
# ----------------- VER MATCHS -----------------

@bot.message_handler(commands=["matches", "matchs"])
def ver_meus_matches(message):
    my_id = message.chat.id

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.nome, p.telegram_id
        FROM perfis p
        WHERE p.telegram_id IN (
            SELECT para_id
            FROM curtidas
            WHERE de_id = ?
        )
        AND p.telegram_id IN (
            SELECT de_id
            FROM curtidas
            WHERE para_id = ?
        )
    """, (my_id, my_id))

    lista_matches = cursor.fetchall()

    conn.close()

    if lista_matches:
        texto = "💌 Seus Matches Atuais:\n\n"

        for nome_match, id_match in lista_matches:
            texto += f"• {nome_match} - Conversar no Privado\n"

        bot.send_message(
            my_id,
            texto,
            parse_mode="Markdown"
        )

    else:
        bot.send_message(
            my_id,
            "💔 Você ainda não tem nenhum Match.\n\nContinue avaliando no /tinder!"
        )


# ----------------- FLUXO DO TINDER -----------------

@bot.message_handler(commands=["start", "tinder"])
def mostrar_proximo_perfil(message):
    my_id = message.chat.id

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM perfis WHERE telegram_id = ?",
        (my_id,)
    )

    if not cursor.fetchone():
        conn.close()

        bot.send_message(
            my_id,
            "⚠️ Você precisa criar um perfil primeiro!\nUse /cadastro.",
            parse_mode="Markdown"
        )
        return

    cursor.execute("""
        SELECT telegram_id,
               nome,
               idade,
               bio,
               foto,
               procura
        FROM perfis
        WHERE telegram_id != ?
        AND telegram_id NOT IN (
            SELECT para_id
            FROM curtidas
            WHERE de_id = ?
        )
        LIMIT 1
    """, (my_id, my_id))

    perfil = cursor.fetchone()

    conn.close()

    if perfil:

        perfil_id, nome, idade, bio, foto, procura = perfil

        markup = InlineKeyboardMarkup()

        markup.row(
            InlineKeyboardButton(
                "❌ Próximo",
                callback_data=f"prox_{perfil_id}"
            ),
            InlineKeyboardButton(
                "❤️ Curtir",
                callback_data=f"curt_{perfil_id}"
            )
        )

        bot.send_photo(
            my_id,
            foto,
            caption=(
                f"{nome}, {idade} anos\n"
                f"🎯 Procura por: {procura}\n\n"
                f"{bio}"
            ),
            reply_markup=markup,
            parse_mode="Markdown"
        )

    else:
        bot.send_message(
            my_id,
            "🌟 Você já viu todos os perfis cadastrados no momento!"
    )
        # ----------------- TRATAMENTO DOS BOTÕES -----------------

@bot.callback_query_handler(
    func=lambda call: call.data.startswith(
        ("curt_", "prox_", "confirmar_", "cancelar_")
    )
)
def tratar_botoes(call):
    my_id = call.message.chat.id

    # --------- APAGAR PERFIL ---------

    if call.data == "confirmar_deletar":

        bot.edit_message_reply_markup(
            my_id,
            call.message.message_id,
            reply_markup=None
        )

        conn = conectar_bd()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM perfis WHERE telegram_id = ?",
            (my_id,)
        )

        cursor.execute(
            "DELETE FROM curtidas WHERE de_id = ? OR para_id = ?",
            (my_id, my_id)
        )

        conn.commit()
        conn.close()

        bot.answer_callback_query(
            call.id,
            "Perfil deletado!",
            show_alert=True
        )

        bot.send_message(
            my_id,
            "❌ Seu perfil foi removido com sucesso."
        )

        return

    elif call.data == "cancelar_deletar":

        bot.edit_message_reply_markup(
            my_id,
            call.message.message_id,
            reply_markup=None
        )

        bot.answer_callback_query(
            call.id,
            "Operação cancelada 😉"
        )

        return

    # --------- CURTIR PERFIL ---------

    elif call.data.startswith("curt_"):

        alvo_id = int(call.data.split("_")[1])

        conn = conectar_bd()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO curtidas VALUES (?, ?)",
                (my_id, alvo_id)
            )
            conn.commit()

        except sqlite3.IntegrityError:
            pass

        cursor.execute(
            """
            SELECT 1
            FROM curtidas
            WHERE de_id = ?
            AND para_id = ?
            """,
            (alvo_id, my_id)
        )

        match = cursor.fetchone()

        cursor.execute(
            "SELECT nome FROM perfis WHERE telegram_id = ?",
            (my_id,)
        )

        resultado = cursor.fetchone()

        meu_nome = resultado[0] if resultado else "Alguém"

        conn.close()

        bot.edit_message_reply_markup(
            my_id,
            call.message.message_id,
            reply_markup=None
        )

        if match:

            bot.answer_callback_query(
                call.id,
                "😍 É UM MATCH!",
                show_alert=True
            )

            bot.send_message(
                my_id,
                "🎉 Vocês se curtiram!\nUse /matches."
            )

            try:
                bot.send_message(
                    alvo_id,
                    f"🎉 Você deu MATCH com {meu_nome}!\nUse /matches."
                )
            except Exception:
                pass

        else:

            bot.answer_callback_query(
                call.id,
                "❤️ Curtido!"
            )

        mostrar_proximo_perfil(call.message)

    # --------- PRÓXIMO PERFIL ---------

    elif call.data.startswith("prox_"):

        bot.edit_message_reply_markup(
            my_id,
            call.message.message_id,
            reply_markup=None
        )

        bot.answer_callback_query(
            call.id,
            "➡️ Próximo perfil"
        )

        mostrar_proximo_perfil(call.message)


# ----------------- DELETAR PERFIL -----------------

@bot.message_handler(commands=["sair", "deletar"])
def confirmar_saida(message):

    user_id = message.chat.id

    markup = InlineKeyboardMarkup()

    markup.row(
        InlineKeyboardButton(
            "✅ Sim, apagar tudo",
            callback_data="confirmar_deletar"
        ),
        InlineKeyboardButton(
            "❌ Não",
            callback_data="cancelar_deletar"
        )
    )

    bot.send_message(
        user_id,
        "⚠️ Tem certeza que deseja apagar seu perfil?",
        reply_markup=markup
    )


# ----------------- INICIAR BOT -----------------

print("Bot iniciado com sucesso!")

bot.infinity_polling(skip_pending=True)
