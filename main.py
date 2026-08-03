import os
import time
import threading
import telebot
import psycopg2 

import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from http.server import HTTPServer, BaseHTTPRequestHandler

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

print("TOKEN existe?", "TOKEN" in os.environ)

TOKEN = os.getenv("TOKEN")

print("TOKEN:", repr(TOKEN))

bot = telebot.TeleBot(TOKEN)

print("TOKEN:", repr(TOKEN))
print("TOKEN carregado?", TOKEN is not None)
print("TESTE BOT INICIANDO")

DB_NAME = "tinder.db"

dados_cadastro = {}
dados_edicao = {}

# =======================================================
# CONFIGURAÇÃO INICIAL DO BANCO DE DADOS
# =======================================================

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

    return psycopg2.connect(
        os.getenv("DATABASE_URL")
    )


def iniciar_banco():

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS perfis(

            telegram_id BIGINT PRIMARY KEY,

            nome TEXT,

            idade INTEGER,

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
        "❤️ *Bem-vindo ao Tinder Rp!*\n\n"
        "Aqui você pode conhecer novas pessoas, "
        "curtir perfis e fazer matches.\n\n"
        "Para começar, crie seu perfil." 
        "Se você não for uma conta de rp não faça conta."
    )

    bot.send_message(
        message.chat.id,
        texto,
        reply_markup=teclado_menu()
    )

# =======================================================
# =======================================================
# # COMANDO: /meus_likes (PERMANENTE)
# =======================================================
@bot.message_handler(commands=["meus_likes"])
def mostrar_meus_likes(message):
    user_id = message.chat.id
    
    try:
        conn = conectar()  # Conecta direto no banco que não apaga
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
                    linhas_meus_likes.append(f"🔹 {nome} (@{user_limpo})")
                else:
                    linhas_meus_likes.append(f"🔹 {nome}")
            lista_meus_likes = "\n".join(linhas_meus_likes)
            texto = f"👤 *Perfis que você curtiu:*\n\n{lista_meus_likes}"
        else:
            texto = "👤 Você ainda não curtiu nenhum perfil."
        
        bot.send_message(user_id, texto, parse_mode="Markdown")
        return

    except Exception as erro:
        bot.send_message(user_id, f"❌ Erro ao acessar seus likes: {erro}")
        return


# =======================================================
# # COMANDO: /quem_me_curtiu (PERMANENTE)
# =======================================================
@bot.message_handler(commands=["quem_me_curtiu"])
def mostrar_quem_me_curtiu(message):
    user_id = message.chat.id
    
    try:
        conn = conectar()  # Conecta direto no banco que não apaga
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
            texto = f"✨ *Perfis que curtiram você:*\n\n{lista_recebidos}"
        else:
            texto = "✨ Ninguém te curtiu ainda. Continue tentando!"
        
        bot.send_message(user_id, texto, parse_mode="Markdown")
        return

    except Exception as erro:
        bot.send_message(user_id, f"❌ Erro ao acessar curtidas recebidas: {erro}")
        return

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

@bot.callback_query_handler(func=lambda call: call.data == "menu_inicio")
def voltar_menu(call):

    try:
        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )
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
            "❓ Ajuda\n\n"
            "📝 Criar Perfil - faça seu cadastro\n"
            "❤️ Tinder - veja perfis\n"
            "👤 Meu Perfil - veja seus dados\n"
            "💌 Matches - veja seus matches\n"
            "✏️ Editar Perfil - edite seu perfil\n"
            "🗑 Excluir Perfil - exclua seu perfil todo\n"
                             )
        # ==========================================================
# CADASTRO
# ==========================================================

@bot.message_handler(commands=["cadastro"])
def iniciar_cadastro(message):

    user_id = message.chat.id

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT telegram_id FROM perfis WHERE telegram_id = %s",
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
    dados_cadastro[user_id]["username"] = message.from_user.username

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

    bot.send_message(
        user_id,
        "📸 Foto recebida, salvando..."
    )

    conn = conectar()
    cursor = conn.cursor()

    bot.send_message(
        user_id,
        "💾 Conectei no banco..."
    )

    try:

        cursor.execute("""
            INSERT INTO perfis(
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
            message.from_user.username
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
            f"❌ Erro ao salvar perfil:\n{e}"
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
            "❌ Você ainda não possui um perfil.\n\nUse /cadastro."
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
        FROM curtidas c1
        WHERE c1.de_id = %s
        AND EXISTS(
            SELECT 1
            FROM curtidas c2
            WHERE c2.de_id = c1.para_id
            AND c2.para_id = %s
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

# =======================================================
# # COMANDO: /matches (PERMANENTE COM @USERNAME)
# =======================================================

@bot.message_handler(commands=["matches"])
def ver_matches(message):
    
    user_id = message.chat.id
    
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Busca os nomes e usernames combinando quem se curtiu mutuamente
        cursor.execute("""
            SELECT p.nome, p.telegram_id, p.username
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
                "💔 Você ainda não tem nenhum match."
            )
            return
            
        texto = "💌 Seus Matches:\n\n"
        
        for nome, id_pessoa, username in matches:
            if username:
                user_limpo = str(username).replace("@", "")
                texto += f"❤️ {nome} (@{user_limpo})\n"
            else:
                texto += f"❤️ {nome}\n"
                
        bot.send_message(user_id, texto)
        return

    except Exception as erro:
        bot.send_message(user_id, f"❌ Erro ao buscar seus matches: {erro}")
        return


# ==========================================================
# MENU EDITAR
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
        f"UPDATE perfis SET {campo}=%s WHERE telegram_id=%s",
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

    # Verifica se o usuário possui perfil
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

    # Escolhe um perfil aleatório
    cursor.execute("""
        SELECT
            telegram_id,
            nome,
            idade,
            bio,
            foto
        FROM perfis

        WHERE telegram_id != %s

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
            "🎉 Você já viu todos os perfis disponíveis.\n\nVolte mais tarde."
        )

        return

    perfil_id, nome, idade, bio, foto = perfil

    markup = InlineKeyboardMarkup(row_width=2)

    markup.add(

        InlineKeyboardButton(
            "❌",
            callback_data=f"nao_{perfil_id}"
        ),

        InlineKeyboardButton(
            "❤️",
            callback_data=f"curtir_{perfil_id}"
        )

    )

    markup.add(

        InlineKeyboardButton(
            "🏠 Menu",
            callback_data="menu_inicio"
        )

    )

    legenda = (
        f"👤 *{nome}*\n"
        f"🎂 {idade} anos\n\n"
        f"📝 {bio}"
    )

    bot.send_photo(

        user_id,

        foto,

        caption=legenda,

        reply_markup=markup

    )

# =======================================================
# # BOTÃO X NÃO CURTIR (CORRIGIDO)
# =======================================================

@bot.callback_query_handler(func=lambda c: c.data.startswith("nao_"))
def nao_curtir(call):
    user_id = call.message.chat.id
    
    try:
        # Pega o ID da pessoa que está sendo pulada a partir do botão
        perfil_id = int(call.data.split("_")[1])
        
        # Conecta e registra na tabela curtidas que você já interagiu com esse perfil
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO curtidas (de_id, para_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (user_id, perfil_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao salvar pulo: {e}")

    bot.answer_callback_query(call.id, "Perfil ignorado.")
    
    try:
        bot.delete_message(user_id, call.message.message_id)
    except:
        pass
        
    mostrar_proximo_perfil(call.message)
    
# =======================================================
# # COMANDO: /tinder E FEED DE PERFIS
# =======================================================

@bot.message_handler(commands=["tinder"])
def mostrar_proximo_perfil(message):
    user_id = message.chat.id if hasattr(message, 'chat') else message.from_user.id
    
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Filtra usando ABS() para ignorar curtidas normais e pulos (IDs negativos)
        cursor.execute("""
            SELECT telegram_id, nome, bio, foto 
            FROM perfis 
            WHERE telegram_id != %s 
            AND telegram_id NOT IN (
                SELECT ABS(para_id) 
                FROM curtidas 
                WHERE de_id = %s
            )
            ORDER BY RANDOM() 
            LIMIT 1;
        """, (user_id, user_id))
        
        perfil = cursor.fetchone()
        conn.close()
        
        if not perfil:
            bot.send_message(user_id, "💔 Não há novos perfis disponíveis no momento.")
            return
            
        perfil_id, nome, bio, foto = perfil
        
        markup = telebot.types.InlineKeyboardMarkup()
        btn_sim = telebot.types.InlineKeyboardButton("❤️ Curtir", callback_data=f"sim_{perfil_id}")
        btn_nao = telebot.types.InlineKeyboardButton("❌ Pular", callback_data=f"nao_{perfil_id}")
        markup.add(btn_sim, btn_nao)
        
        texto = f"🔥 *{nome}*\n\n📝 {bio}"
        
        if foto:
            bot.send_photo(user_id, foto, caption=texto, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(user_id, texto, parse_mode="Markdown", reply_markup=markup)
            
    except Exception as e:
        print(f"Erro ao buscar perfil: {e}")
        bot.send_message(user_id, "❌ Houve um erro ao carregar o próximo perfil.")

# =======================================================
# # BOTÃO: CURTIR (❤️)
# =======================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("sim_"))
def curtir_perfil(call):
    user_id = call.message.chat.id
    perfil_id = int(call.data.split("_"))
    
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Salva o Like real (ID positivo)
        cursor.execute("""
            INSERT INTO curtidas (de_id, para_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (user_id, perfil_id))
        conn.commit()
        
        # Verifica se deu Match legítimo
        cursor.execute("""
            SELECT nome, username FROM perfis 
            WHERE telegram_id = %s AND telegram_id IN (
                SELECT de_id FROM curtidas WHERE para_id = %s AND para_id > 0
            )
        """, (perfil_id, user_id))
        
        match = cursor.fetchone()
        conn.close()
        
        bot.answer_callback_query(call.id, "Você curtiu o perfil!")
        
        if match:
            nome_match, user_match = match
            arroba = f" (@{str(user_match).replace('@', '')})" if user_match else ""
            bot.send_message(user_id, f"🎉 *É um MATCH!* Você e *{nome_match}*{arroba} se curtiram mutuamente!")
            
    except Exception as e:
        print(f"Erro ao curtir: {e}")
        
    try:
        bot.delete_message(user_id, call.message.message_id)
    except:
        pass
        
    mostrar_proximo_perfil(call.message)

# =======================================================
# # BOTÃO: REJEITAR / PULAR (❌)
# =======================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("nao_"))
def nao_curtir(call):
    user_id = call.message.chat.id
    perfil_id = int(call.data.split("_"))
    
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Salva como NEGATIVO para o /matches ignorar, mas o feed não repetir
        cursor.execute("""
            INSERT INTO curtidas (de_id, para_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (user_id, -perfil_id))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao salvar pulo: {e}")

    bot.answer_callback_query(call.id, "Perfil ignorado.")
    
    try:
        bot.delete_message(user_id, call.message.message_id)
# =======================================================
# # COMANDO: /tinder E FEED DE PERFIS
# =======================================================
@bot.message_handler(commands=["tinder"])
def mostrar_proximo_perfil(message):
    user_id = message.chat.id if hasattr(message, 'chat') else message.from_user.id
    
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Filtra usando ABS() para ignorar curtidas normais e pulos (IDs negativos)
        cursor.execute("""
            SELECT telegram_id, nome, bio, foto 
            FROM perfis 
            WHERE telegram_id != %s 
            AND telegram_id NOT IN (
                SELECT ABS(para_id) 
                FROM curtidas 
                WHERE de_id = %s
            )
            ORDER BY RANDOM() 
            LIMIT 1;
        """, (user_id, user_id))
        
        perfil = cursor.fetchone()
        conn.close()
        
        if not perfil:
            bot.send_message(user_id, "💔 Não há novos perfis disponíveis no momento.")
            return
            
        perfil_id, nome, bio, foto = perfil
        
        markup = telebot.types.InlineKeyboardMarkup()
        btn_sim = telebot.types.InlineKeyboardButton("❤️ Curtir", callback_data=f"sim_{perfil_id}")
        btn_nao = telebot.types.InlineKeyboardButton("❌ Pular", callback_data=f"nao_{perfil_id}")
        markup.add(btn_sim, btn_nao)
        
        texto = f"🔥 *{nome}*\n\n📝 {bio}"
        
        if foto:
            bot.send_photo(user_id, foto, caption=texto, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(user_id, texto, parse_mode="Markdown", reply_markup=markup)
            
    except Exception as e:
        print(f"Erro ao buscar perfil: {e}")
        bot.send_message(user_id, "❌ Houve um erro ao carregar o próximo perfil.")

# =======================================================
# # COMANDO: /tinder E FEED DE PERFIS
# =======================================================
@bot.message_handler(commands=["tinder"])
def mostrar_proximo_perfil(message):
    user_id = message.chat.id if hasattr(message, 'chat') else message.from_user.id
    
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Filtra usando ABS() para ignorar curtidas normais e pulos (IDs negativos)
        cursor.execute("""
            SELECT telegram_id, nome, bio, foto 
            FROM perfis 
            WHERE telegram_id != %s 
            AND telegram_id NOT IN (
                SELECT ABS(para_id) 
                FROM curtidas 
                WHERE de_id = %s
            )
            ORDER BY RANDOM() 
            LIMIT 1;
        """, (user_id, user_id))
        
        perfil = cursor.fetchone()
        conn.close()
        
        if not perfil:
            bot.send_message(user_id, "💔 Não há novos perfis disponíveis no momento.")
            return
            
        perfil_id, nome, bio, foto = perfil
        
        markup = telebot.types.InlineKeyboardMarkup()
        btn_sim = telebot.types.InlineKeyboardButton("❤️ Curtir", callback_data=f"sim_{perfil_id}")
        btn_nao = telebot.types.InlineKeyboardButton("❌ Pular", callback_data=f"nao_{perfil_id}")
        markup.add(btn_sim, btn_nao)
        
        texto = f"🔥 *{nome}*\n\n📝 {bio}"
        
        if foto:
            bot.send_photo(user_id, foto, caption=texto, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(user_id, texto, parse_mode="Markdown", reply_markup=markup)
            
    except Exception as e:
        print(f"Erro ao buscar perfil: {e}")
        bot.send_message(user_id, "❌ Houve um erro ao carregar o próximo perfil.")

# =======================================================
# # BOTÃO: CURTIR (❤️)
# =======================================================
@bot.callback_query_handler(func=lambda c: c.data.startswith("sim_"))
def curtir_perfil(call):
    user_id = call.message.chat.id
    
    try:
        # Pega o ID da pessoa separando corretamente por "_"
        perfil_id = int(call.data.split("_"))
        
        conn = conectar()
        cursor = conn.cursor()
        
        # Salva o Like real (ID positivo)
        cursor.execute("""
            INSERT INTO curtidas (de_id, para_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING;
        """, (user_id, perfil_id))
        conn.commit()
        
        # Verifica se deu Match legítimo
        cursor.execute("""
            SELECT nome, username FROM perfis 
            WHERE telegram_id = %s AND telegram_id IN (
                SELECT de_id FROM curtidas WHERE para_id = %s AND para_id > 0
            )
        """, (perfil_id, user_id))
        
        match = cursor.fetchone()
        conn.close()
        
        bot.answer_callback_query(call.id, "Você curtiu o perfil!")
        
        if match:
            nome_match, user_match = match
            arroba = f" (@{str(user_match).replace('@', '')})" if user_match else ""
            bot.send_message(user_id, f"🎉 *É um MATCH!* Você e *{nome_match}*{arroba} se curtiram mutuamente!")
            
    except Exception as e:
        print(f"Erro ao curtir: {e}")
        bot.answer_callback_query(call.id, "Erro ao processar curtida.")
        
    try:
        bot.delete_message(user_id, call.message.message_id)
    except:
        pass
        
    mostrar_proximo_perfil(call.message)

# =======================================================
# # COMANDO: /matches (PERMANENTE COM FILTRO DE PULO)
# =======================================================
@bot.message_handler(commands=["matches"])
def ver_meus_matches(message):
    user_id = message.chat.id
    
    conn = conectar()
    cursor = conn.cursor()
    
    # Filtra trazendo apenas curtidas reais maiores que zero (> 0)
    cursor.execute("""
        SELECT p.nome, p.username
        FROM perfis p
        WHERE p.telegram_id IN (
            SELECT para_id
            FROM curtidas
            WHERE de_id = %s AND para_id > 0
        )
        AND p.telegram_id IN (
            SELECT de_id
            FROM curtidas
            WHERE para_id = %s AND de_id > 0
        )
        ORDER BY p.nome
    """, (user_id, user_id))
    
    matches = cursor.fetchall()
    conn.close()
    
    if not matches:
        bot.send_message(
            user_id,
            "💖 Você ainda não possui nenhum match."
        )
        return
        
    texto = "💌 *Seus Matches:*\n\n"
    
    for pessoa in matches:
        nome = pessoa[0]
        username = pessoa[1]
        
        if username:
            user_limpo = str(username).replace("@", "")
            texto += f"❤️ {nome} (@{user_limpo})\n"
        else:
            texto += f"❤️ {nome}\n"
            
    # Mantém o teclado de botões original que você já tinha criado
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("❤️ Continuar", callback_data="continuar_tinder"),
        InlineKeyboardButton("🏠 Menu", callback_data="menu_inicio")
    )
    
    bot.send_message(
        user_id,
        texto,
        parse_mode="Markdown",
        reply_markup=markup
    )

# =======================================================
# COMANDO TEMPORÁRIO: /limpar_antigos
# =======================================================
@bot.message_handler(commands=["limpar_antigos"])
def limpar_historico_antigo(message):
    user_id = message.chat.id
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Apaga registros antigos para limpar o histórico com bugs
        cursor.execute("DELETE FROM curtidas WHERE de_id = %s OR para_id = %s;", (user_id, user_id))
        
        conn.commit()
        conn.close()
        
        bot.send_message(user_id, "🧹 *Faxina Concluída!* Seu histórico antigo de interações foi zerado. Agora o sistema novo de Likes e Pulos funcionará perfeitamente sem misturar nada.")
    except Exception as e:
        bot.send_message(user_id, f"❌ Erro na faxina: {e}")

# ==========================================================
# BOTÕES DO MATCH
# ==========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "continuar_tinder"
)
def continuar_tinder(call):

    try:
        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )
    except:
        pass

    mostrar_proximo_perfil(call.message)


# ==========================================================
# MENU
# ==========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "menu_inicio"
)
def voltar_menu(call):

    try:
        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )
    except:
        pass

    enviar_menu(call.message.chat.id)
    # ==========================================================
# ESTATÍSTICAS DO PERFIL
# ==========================================================

@bot.message_handler(commands=["stats"])
def estatisticas_perfil(message):

    user_id = message.chat.id

    conn = conectar()
    cursor = conn.cursor()

    # Curtidas recebidas
    cursor.execute("""
        SELECT COUNT(*)
        FROM curtidas
        WHERE para_id=%s
    """, (user_id,))

    curtidas = cursor.fetchone()[0]


    # Curtidas enviadas
    cursor.execute("""
        SELECT COUNT(*)
        FROM curtidas
        WHERE de_id=%s
    """, (user_id,))

    enviadas = cursor.fetchone()[0]


    # Matches
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
        "📊 *Estatísticas do Perfil*\n\n"
        f"❤️ Curtidas recebidas: {curtidas}\n"
        f"💌 Matches: {matches}\n"
        f"🔥 Perfis curtidos por você: {enviadas}"
    )


    markup = InlineKeyboardMarkup()

    markup.add(
        InlineKeyboardButton(
            "👤 Ver Perfil",
            callback_data="menu_perfil"
        ),

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
# MELHORAR VISUAL DO PERFIL
# ==========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "menu_perfil"
)
def abrir_perfil_botao(call):

    try:
        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )
    except:
        pass

    ver_meu_perfil(call.message)
    # ==========================================================
# EXCLUIR PERFIL
# ==========================================================

@bot.message_handler(commands=["deletar"])
def confirmar_deletar(message):

    user_id = message.chat.id

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT telegram_id FROM perfis WHERE telegram_id=%s",
        (user_id,)
    )

    existe = cursor.fetchone()

    conn.close()


    if not existe:

        bot.send_message(
            user_id,
            "❌ Você não possui um perfil para excluir."
        )

        return


    markup = InlineKeyboardMarkup(row_width=2)

    markup.add(

        InlineKeyboardButton(
            "✅ Sim, apagar",
            callback_data="confirmar_delete"
        ),

        InlineKeyboardButton(
            "❌ Cancelar",
            callback_data="cancelar_delete"
        )

    )


    bot.send_message(

        user_id,

        "⚠️ *Tem certeza que deseja apagar seu perfil?*\n\n"
        "Essa ação não pode ser desfeita.",

        reply_markup=markup

    )


# ==========================================================
# CONFIRMAÇÃO DE EXCLUSÃO
# ==========================================================

@bot.callback_query_handler(
    func=lambda c: c.data in [
        "confirmar_delete",
        "cancelar_delete"
    ]
)
def processar_delete(call):

    user_id = call.message.chat.id


    if call.data == "cancelar_delete":

        bot.answer_callback_query(
            call.id,
            "Cancelado."
        )

        bot.edit_message_text(
            "✅ Exclusão cancelada.",
            user_id,
            call.message.message_id
        )

        return



    # Apagar tudo

    conn = conectar()
    cursor = conn.cursor()


    cursor.execute(
        """
        DELETE FROM perfis
        WHERE telegram_id=%s
        """,
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


    bot.answer_callback_query(
        call.id,
        "Perfil apagado!"
    )


    bot.edit_message_text(

        "🗑️ *Seu perfil foi removido com sucesso.*\n\n"
        "Você pode criar outro usando /cadastro.",

        user_id,

        call.message.message_id

    )
    # ==========================================================
# FUNÇÃO DE VERIFICAÇÃO DE PERFIL
# ==========================================================

def possui_perfil(user_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT telegram_id
        FROM perfis
        WHERE telegram_id=%s
        """,
        (user_id,)
    )

    resultado = cursor.fetchone()

    conn.close()

    return resultado is not None


# ==========================================================
# PROTEÇÃO DO TINDER
# ==========================================================

def verificar_tinder(message):

    user_id = message.chat.id

    if not possui_perfil(user_id):

        bot.send_message(
            user_id,
            "⚠️ Você precisa criar um perfil antes.\n\nUse /cadastro."
        )

        return False

    return True


# ==========================================================
# BOTÃO CONTINUAR TINDER
# ==========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "continuar_tinder"
)
def continuar_tinder_botao(call):

    try:

        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )

    except:
        pass


    mostrar_proximo_perfil(call.message)



# ==========================================================
# COMANDO TINDER COM PROTEÇÃO
# ==========================================================

@bot.message_handler(commands=["ver"])
def abrir_tinder(message):

    if verificar_tinder(message):

        mostrar_proximo_perfil(message)



# ==========================================================
# TRATAMENTO DE ERROS GERAIS
# ==========================================================

@bot.message_handler(
    content_types=[
        "text",
        "photo",
        "sticker",
        "video"
    ]
)
def mensagens_sem_funcao(message):

    comandos = [
        "/start",
        "/cadastro",
        "/perfil",
        "/editar",
        "/tinder",
        "/matches",
        "/stats",
        "/deletar"
    ]


    if message.text in comandos:

        return


    # Não responde durante cadastros
    if message.chat.id in dados_cadastro:

        return


    bot.send_message(

        message.chat.id,

        "🤖 Use o menu abaixo para navegar.",

        reply_markup=teclado_menu()

        )
    # ==========================================================
# MENU PRINCIPAL
# ==========================================================

@bot.message_handler(commands=["menu"])
def comando_menu(message):

    enviar_menu(message.chat.id)


# ==========================================================
# MENU ATUALIZADO
# ==========================================================

def enviar_menu(chat_id):

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
            "✏️ Editar",
            callback_data="menu_editar"
        ),

        InlineKeyboardButton(
            "💌 Matches",
            callback_data="menu_matches"
        )

    )


    markup.add(

        InlineKeyboardButton(
            "📊 Estatísticas",
            callback_data="menu_stats"
        ),

        InlineKeyboardButton(
            "🗑️ Deletar",
            callback_data="menu_deletar"
        )

    )


    texto = (
        "🏠 *Menu Principal*\n\n"
        "Escolha uma opção:\n\n"
        "❤️ Conheça pessoas\n"
        "👤 Veja seu perfil\n"
        "✏️ Atualize suas informações\n"
        "💌 Confira seus matches"
    )


    bot.send_message(

        chat_id,

        texto,

        reply_markup=markup

    )


# ==========================================================
# NOVOS BOTÕES DO MENU
# ==========================================================

@bot.callback_query_handler(
    func=lambda c: c.data.startswith("menu_")
)
def botoes_menu(call):

    user_id = call.message.chat.id


    bot.answer_callback_query(call.id)


    if call.data == "menu_stats":

        estatisticas_perfil(call.message)


    elif call.data == "menu_tinder":

        mostrar_proximo_perfil(call.message)


    elif call.data == "menu_perfil":

        ver_meu_perfil(call.message)


    elif call.data == "menu_editar":

        menu_editar(call.message)


    elif call.data == "menu_matches":

        ver_meus_matches(call.message)


    elif call.data == "menu_deletar":

        confirmar_deletar(call.message)



# ==========================================================
# COMANDO AJUDA MELHORADO
# ==========================================================

@bot.message_handler(commands=["ajuda"])
def comando_ajuda(message):

    texto = (
        "📖 *Ajuda do Bot*\n\n"

        "❤️ /tinder - Ver perfis\n"
        "👤 /perfil - Seu perfil\n"
        "✏️ /editar - Editar informações\n"
        "💌 /matches - Seus matches\n"
        "📊 /stats - Estatísticas\n"
        "🗑️ /deletar - Apagar perfil\n"
        "🏠 /menu - Menu principal\n\n"

        "Boa sorte nos matches! ❤️"
    )


    bot.send_message(
        message.chat.id,
        texto
    )
    # ==========================================================
# LIMPEZA DE DADOS TEMPORÁRIOS
# ==========================================================

def limpar_dados_temporarios():

    dados_cadastro.clear()
    dados_edicao.clear()


# ==========================================================
# COMANDO REINICIAR MENU
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


# ==========================================================
# BOTÃO CANCELAR
# ==========================================================

@bot.callback_query_handler(
    func=lambda c: c.data == "cancelar"
)
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
        "✅ Bot online e funcionando!"
    )
        
# ==========================================================
# FUNÇÃO DE INICIAR BOT
# ==========================================================

def iniciar_bot():

    while True:

        try:

            print("🤖 Bot iniciado!")

            bot.infinity_polling(
                timeout=60,
                long_polling_timeout=60,
                skip_pending=True
            )

            print("⚠️ O polling terminou sozinho!")

        except Exception as erro:

            print(f"Erro no bot: {erro}")

            time.sleep(5)
# ==========================================================
# EXECUTAR BOT
# ==========================================================

if __name__ == "__main__":

    print("TESTE CHEGOU NO FINAL DO ARQUIVO")

    iniciar_bot()
