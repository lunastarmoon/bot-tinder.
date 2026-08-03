import os
import time
import threading
import telebot
import psycopg2
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from http.server import HTTPServer, BaseHTTPRequestHandler

# CONFIGURAÇÕES
print("TOKEN existe?", "TOKEN" in os.environ)
TOKEN = os.environ.get("TOKEN")
print("TOKEN:", repr(TOKEN))
bot = telebot.TeleBot(TOKEN)
print("TOKEN:", repr(TOKEN))
print("TOKEN carregado?", TOKEN is not None)
print("TESTE BOT INICIANDO")

DB_NAME = "tinder.db"
dados_cadastro = {}
dados_edicao = {}

# CONFIGURAÇÃO INICIAL DO BANCO DE DADOS
# SERVIDOR HTTP (RENDER)
class ServidorHTTP(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot tinder Online!")

def iniciar_servidor():
    porta = int(os.environ.get("PORT", 8000))
    servidor = HTTPServer(("0.0.0.0", porta), ServidorHTTP)
    servidor.serve_forever()

threading.Thread(target=iniciar_servidor, daemon=True).start()

# BANCO DE DADOS
def conectar():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

def iniciar_banco():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfis (
            telegram_id BIGINT PRIMARY KEY,
            nome TEXT,
            idade INTEGER,
            bio TEXT,
            foto TEXT,
            username TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS curtidas (
            de_id BIGINT,
            para_id BIGINT,
            PRIMARY KEY(de_id, para_id)
        );
    """)
    conn.commit()
    conn.close()

iniciar_banco()

# TECLADOS
def teclado_menu():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("❤️ Tinder", callback_data="menu_tinder"),
        InlineKeyboardButton("👤 Meu Perfil", callback_data="menu_perfil")
    )
    markup.add(
        InlineKeyboardButton("📊 Matches", callback_data="menu_matches"),
        InlineKeyboardButton("📝 Editar Perfil", callback_data="menu_editar")
    )
    markup.add(
        InlineKeyboardButton("➕ Criar Perfil", callback_data="menu_cadastro"),
        InlineKeyboardButton("❌ Excluir Perfil", callback_data="menu_deletar")
    )
    markup.add(
        InlineKeyboardButton("❓ Ajuda", callback_data="menu_ajuda")
    )
    return markup

# MENU PRINCIPAL
def enviar_menu(chat_id):
    bot.send_message(
        chat_id,
        "📱 *Menu Principal*\n\nEscolha uma opção abaixo:",
        reply_markup=teclado_menu()
    )

# START
@bot.message_handler(commands=["start"])
def start(message):
    texto = (
        "👋 Bem-vindo ao Tinder RP!\n\n"
        "Aqui você pode conhecer novas pessoas,\n"
        "curtir perfis e fazer matches.\n"
        "Para começar, crie seu perfil.\n"
        "Se você não for uma conta de rp não faça conta."
    )
    bot.send_message(message.chat.id, texto, reply_markup=teclado_menu())

# COMANDO: /meus_likes (PERMANENTE)
@bot.message_handler(commands=["meus_likes"])
def mostrar_meus_likes(message):
    user_id = message.chat.id
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.nome, p.username
            FROM curtidas c
            JOIN perfis p ON c.para_id = p.telegram_id
            WHERE c.de_id = %s
        """, (user_id,))
        meus_likes = cursor.fetchall()
        conn.close()

        if meus_likes:
            linhas_meus_likes = []
            for nome, username in meus_likes:
                if username:
                    user_limpo = str(username).replace("@", "")
                    linhas_meus_likes.append(f"❤️ {nome} (@{user_limpo})")
                else:
                    linhas_meus_likes.append(f"❤️ {nome}")
            lista_meus_likes = "\n".join(linhas_meus_likes)
            texto = f"✨ *Perfis que você curtiu:*\n\n{lista_meus_likes}"
        else:
            texto = "🥺 Você ainda não curtiu nenhum perfil."
        bot.send_message(user_id, texto, parse_mode="Markdown")
    except Exception as erro:
        bot.send_message(user_id, f"❌ Erro ao acessar seus likes: {erro}")

# COMANDO: /quem_me_curtiu (PERMANENTE)
@bot.message_handler(commands=["quem_me_curtiu"])
def mostrar_quem_me_curtiu(message):
    user_id = message.chat.id
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.nome, p.username
            FROM curtidas c
            JOIN perfis p ON c.de_id = p.telegram_id
            WHERE c.para_id = %s
        """, (user_id,))
        likes_recebidos = cursor.fetchall()
        conn.close()

        if likes_recebidos:
            linhas_recebidos = []
            for nome, username in likes_recebidos:
                if username:
                    user_limpo = str(username).replace("@", "")
                    linhas_recebidos.append(f"✨ {nome} (@{user_limpo})")
                else:
                    linhas_recebidos.append(f"✨ {nome}")
            lista_recebidos = "\n".join(linhas_recebidos)
            texto = f"💖 *Perfis que curtiram você:*\n\n{lista_recebidos}"
        else:
            texto = "✨ Ninguém te curtiu ainda. Continue tentando!"
        bot.send_message(user_id, texto, parse_mode="Markdown")
    except Exception as erro:
        bot.send_message(user_id, f"❌ Erro ao acessar curtidas recebidas: {erro}")

# AJUDA
@bot.message_handler(commands=["ajuda"])
def ajuda(message):
    texto = (
        "🤖 *Comandos disponíveis:*\n\n"
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

# CALLBACK DO MENU
@bot.callback_query_handler(func=lambda call: call.data == "menu_inicio")
def voltar_menu(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    enviar_menu(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def botoes_menu(call):
    bot.answer_callback_query(call.id)
    if call.data == "menu_tinder":
        mostrar_proximo_perfil(call.message)
    elif call.data == "menu_perfil":
        ver_meu_perfil(call.message)
    elif call.data == "menu_editar":
        menu_editar(call.message)
    elif call.data == "menu_matches":
        ver_meus_matches(call.message)
    elif call.data == "menu_cadastro":
        iniciar_cadastro(call.message)
    elif call.data == "menu_stats":
        estatisticas_perfil(call.message)
    elif call.data == "menu_deletar":
        confirmar_deletar(call.message)
    elif call.data == "menu_ajuda":
        bot.send_message(
            call.message.chat.id,
            "❓ *Ajuda*\n\n"
            "📩 Criar Perfil - faça seu cadastro\n"
            "🔥 Tinder - veja perfis\n"
            "👤 Meu Perfil - veja seus dados\n"
            "💬 Matches - veja seus matches\n"
            "✏️ Editar Perfil - edite seu perfil\n"
            "🗑️ Excluir Perfil - exclua seu perfil todo\n"
        )

# CADASTRO
@bot.message_handler(commands=["cadastro"])
def iniciar_cadastro(message):
    user_id = message.chat.id
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM perfis WHERE telegram_id = %s", (user_id,))
    existe = cursor.fetchone()
    conn.close()

    if existe:
        bot.send_message(user_id, "⚠️ Você já possui um perfil. Use /editar para alterá-lo.")
        return

    dados_cadastro[user_id] = {}
    msg = bot.send_message(user_id, "📝 Qual é o seu nome?")
    bot.register_next_step_handler(msg, salvar_nome)

def salvar_nome(message):
    user_id = message.chat.id
    if user_id not in dados_cadastro:
        return
    nome = message.text.strip()
    if len(nome) < 2:
        msg = bot.send_message(user_id, "❌ Digite um nome válido.")
        bot.register_next_step_handler(msg, salvar_nome)
        return
    dados_cadastro[user_id]["nome"] = nome
    dados_cadastro[user_id]["username"] = message.from_user.username
    msg = bot.send_message(user_id, "🔢 Qual é a sua idade?")
    bot.register_next_step_handler(msg, salvar_idade)

def salvar_idade(message):
    user_id = message.chat.id
    if user_id not in dados_cadastro:
        return
    try:
        idade = int(message.text)
    except ValueError:
        msg = bot.send_message(user_id, "❌ Digite apenas números.")
        bot.register_next_step_handler(msg, salvar_idade)
        return

    if idade < 18:
        bot.send_message(user_id, "🔞 Este bot é permitido apenas para maiores de 18 anos.")
        del dados_cadastro[user_id]
        return

    dados_cadastro[user_id]["idade"] = idade
    msg = bot.send_message(user_id, "✍️ Escreva uma bio sobre você:")
    bot.register_next_step_handler(msg, salvar_bio)

def salvar_bio(message):
    user_id = message.chat.id
    if user_id not in dados_cadastro:
        return
    bio = message.text.strip()
    if len(bio) < 5:
        msg = bot.send_message(user_id, "❌ Escreva uma bio um pouco maior.")
        bot.register_next_step_handler(msg, salvar_bio)
        return
    dados_cadastro[user_id]["bio"] = bio
    msg = bot.send_message(user_id, "📸 Agora envie uma foto de perfil:")
    bot.register_next_step_handler(msg, salvar_foto)

def salvar_foto(message):
    user_id = message.chat.id
    if user_id not in dados_cadastro:
        return
    if message.content_type != "photo":
        msg = bot.send_message(user_id, "❌ Envie uma foto.")
        bot.register_next_step_handler(msg, salvar_foto)
        return

    foto = message.photo[-1].file_id
    bot.send_message(user_id, "⏳ Foto recebida, salvando...")

        conn = conectar()
        cursor = conn.cursor()

    bot.send_message(user_id, "⚙️ Conectando ao banco...")

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

    except Exception as e:

        bot.send_message(
            user_id,
            f"❌ Erro ao salvar perfil: {e}"
        )

    finally:
        conn.close()

    
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
        WHERE telegram_id = %s
    """, (user_id,))

    perfil = cursor.fetchone()

    conn.close()

    if not perfil:

        bot.send_message(
            user_id,
            "❌ Você ainda não possui um perfil. Digite /cadastro."
        )

        return

    nome, idade, bio, foto = perfil

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM curtidas
        WHERE para_id = %s
    """, (user_id,))

    curtidas = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM curtidas
        WHERE de_id = %s
        AND para_id IN (
            SELECT de_id
            FROM curtidas
            WHERE para_id = %s
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
        f"👤 {nome}, {idade}\n"
        f"📝 {bio}\n\n"
        f"💖 Curtidas: {curtidas}\n"
        f"💬 Matches: {matches}"
    )

    bot.send_photo(
        user_id,
        foto,
        caption=legenda,
        reply_markup=markup
    )


# ==========================================================
# COMANDO: /matches
# ==========================================================

@bot.message_handler(commands=["matches"])
def ver_meus_matches(message):

    user_id = message.chat.id

    try:

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.nome, p.username
            FROM perfis p
            WHERE p.telegram_id IN (
                SELECT para_id
                FROM curtidas
                WHERE de_id = %s
            )
            AND p.telegram_id IN (
                SELECT de_id
                FROM curtidas
                WHERE para_id = %s
            )
        """, (user_id, user_id))

        matches = cursor.fetchall()

        conn.close()

        if not matches:

            bot.send_message(
                user_id,
                "❤️ Você ainda não tem nenhum match."
            )

            return

        texto = "✨ Seus Matches:\n\n"

        for nome, username in matches:

            if username:

                user_limpo = str(username).replace("@", "")

                texto += f"❤️ {nome} (@{user_limpo})\n"

            else:

                texto += f"❤️ {nome}\n"

        bot.send_message(
            user_id,
            texto
        )

    except Exception as erro:

        bot.send_message(
            user_id,
            f"❌ Erro ao buscar seus matches: {erro}"
    )

# ==========================================================
# MENU EDITAR
# ==========================================================

@bot.message_handler(commands=["editar"])
def abrir_editor(message):

    user_id = message.chat.id

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT telegram_id FROM perfis WHERE telegram_id = %s",
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
            "✍️ Nome",
            callback_data="editar_nome"
        ),
        InlineKeyboardButton(
            "🔢 Idade",
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
        "⚙️ Escolha o que deseja editar:",
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

        msg = bot.send_message(
            user_id,
            "✍️ Digite o novo nome:"
        )

        bot.register_next_step_handler(msg, salvar_edicao)

    elif call.data == "editar_idade":

        dados_edicao[user_id] = "idade"

        msg = bot.send_message(
            user_id,
            "🔢 Digite a nova idade:"
        )

        bot.register_next_step_handler(msg, salvar_edicao)

    elif call.data == "editar_bio":

        dados_edicao[user_id] = "bio"

        msg = bot.send_message(
            user_id,
            "📝 Digite a nova bio:"
        )

        bot.register_next_step_handler(msg, salvar_edicao)

    elif call.data == "editar_foto":

        dados_edicao[user_id] = "foto"

        msg = bot.send_message(
            user_id,
            "📸 Envie a nova foto:"
        )

        bot.register_next_step_handler(msg, salvar_edicao_foto)


# ==========================================================
# SALVAR EDIÇÃO
# ==========================================================

def salvar_edicao(message):

    user_id = message.chat.id

    if user_id not in dados_edicao:
        return

    campo = dados_edicao[user_id]
    valor = message.text.strip()

    if campo == "idade":

        try:
            valor = int(valor)

        except ValueError:

            bot.send_message(
                user_id,
                "❌ Digite apenas números."
            )

            return

        if valor < 18:

            bot.send_message(
                user_id,
                "🔞 A idade mínima é 18 anos."
            )

            return

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        f"UPDATE perfis SET {campo} = %s WHERE telegram_id = %s",
        (valor, user_id)
    )

    conn.commit()
    conn.close()

    del dados_edicao[user_id]

    bot.send_message(
        user_id,
        "✅ Perfil atualizado com sucesso!"
    )


# ==========================================================
# SALVAR FOTO
# ==========================================================

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
        "UPDATE perfis SET foto = %s WHERE telegram_id = %s",
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

    cursor.execute(
        "SELECT telegram_id FROM perfis WHERE telegram_id = %s",
        (user_id,)
    )

    if not cursor.fetchone():

        conn.close()

        bot.send_message(
            user_id,
            "❌ Você precisa criar um perfil primeiro.\n\nUse /cadastro."
        )

        return

    cursor.execute("""
        SELECT
            telegram_id,
            nome,
            idade,
            bio,
            foto
        FROM perfis
        WHERE telegram_id != %s
        AND telegram_id NOT IN (
            SELECT para_id
            FROM curtidas
            WHERE de_id = %s
        )
        ORDER BY RANDOM()
        LIMIT 1
    """, (user_id, user_id))

    perfil = cursor.fetchone()

    conn.close()

    if not perfil:

        bot.send_message(
            user_id,
            "✨ Você já viu todos os perfis disponíveis.\n\nVolte mais tarde."
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
            "🏠 Menu",
            callback_data="menu_inicio"
        )
    )

    legenda = (
        f"👤 {nome}, {idade}\n\n"
        f"📝 {bio}"
    )

    bot.send_photo(
        user_id,
        foto,
        caption=legenda,
        reply_markup=markup
    )

    # ==========================================================
# CALLBACKS DO FEED
# ==========================================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("nao_"))
def nao_curtir(call):

    user_id = call.message.chat.id
    perfil_id = int(call.data.split("_")[1])

    try:

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO curtidas (de_id, para_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (user_id, perfil_id))

        conn.commit()
        conn.close()

    except Exception as e:

        print(f"Erro ao salvar pulo: {e}")

    bot.answer_callback_query(
        call.id,
        "Perfil ignorado."
    )

    try:

        bot.delete_message(
            user_id,
            call.message.message_id
        )

    except Exception:
        pass

    mostrar_proximo_perfil(call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith("sim_"))
def curtir_perfil(call):

    user_id = call.message.chat.id
    perfil_id = int(call.data.split("_")[1])

    try:

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO curtidas (de_id, para_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (user_id, perfil_id))

        conn.commit()

        cursor.execute("""
            SELECT telegram_id
            FROM curtidas
            WHERE de_id = %s
            AND para_id = %s
        """, (perfil_id, user_id))

        match = cursor.fetchone()

        conn.close()

        if match:

            bot.send_message(
                user_id,
                "🎉 É um match! Use /matches para ver os detalhes."
            )

            bot.send_message(
                perfil_id,
                "🎉 Você tem um novo match!"
            )

    except Exception as e:

        print(f"Erro ao salvar curtida: {e}")

    bot.answer_callback_query(
        call.id,
        "Você curtiu o perfil!"
    )

    try:

        bot.delete_message(
            user_id,
            call.message.message_id
        )

    except Exception:
        pass

    mostrar_proximo_perfil(call.message)


# ==========================================================
# ESTATÍSTICAS DO PERFIL
# ==========================================================

@bot.message_handler(commands=["stats"])
def estatisticas_perfil(message):

    user_id = message.chat.id

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM curtidas
        WHERE para_id = %s
    """, (user_id,))

    curtidas = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM curtidas
        WHERE de_id = %s
        AND para_id IN (
            SELECT de_id
            FROM curtidas
            WHERE para_id = %s
        )
    """, (user_id, user_id))

    matches = cursor.fetchone()[0]

    conn.close()

    texto = (
        "📊 *Suas Estatísticas*\n\n"
        f"💖 Curtidas recebidas: {curtidas}\n"
        f"💬 Matches combinados: {matches}"
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
        reply_markup=markup,
        parse_mode="Markdown"
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
            "✅ Sim, apagar",
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
            "DELETE FROM perfis WHERE telegram_id = %s",
            (user_id,)
        )

        cursor.execute(
            "DELETE FROM curtidas WHERE de_id = %s OR para_id = %s",
            (user_id, user_id)
        )

       # ==========================================================
# BOTÃO CANCELAR
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
        del dados_cadastro[user_id]

    if user_id in dados_edicao:
        del dados_edicao[user_id]

    bot.answer_callback_query(
        call.id,
        "Cancelado"
    )

    enviar_menu(user_id)


# ==========================================================
# MENSAGEM DE STATUS
# ==========================================================

@bot.message_handler(commands=["status"])
def status_bot(message):

    bot.send_message(
        message.chat.id,
        "🚀 Bot online e funcionando!"
    )


# ==========================================================
# FUNÇÃO DE INICIAR BOT
# ==========================================================

def iniciar_bot():

    while True:

        try:

            print("🤖 Bot iniciado...")

            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=20,
                skip_pending=True
            )

        except Exception as erro:

            print(f"⚠️ Erro no bot: {erro}")

            time.sleep(5)


# ==========================================================
# EXECUTAR BOT
# ==========================================================

if __name__ == "__main__":

    iniciar_bot()
