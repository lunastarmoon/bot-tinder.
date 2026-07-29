import os
import sqlite3
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- TRUQUE DE PORTA PARA O RENDER NÃO DERRUBAR O BOT ---
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
            bio TEXT, 
            foto TEXT,
            genero TEXT,
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

# ----------------- FLUXO DE CADASTRO ATUALIZADO -----------------

@bot.message_handler(commands=['cadastro'])
def iniciar_cadastro(message):
    id_usuario = message.chat.id
    dados_cadastro[id_usuario] = {} 
    bot.send_message(id_usuario, "👋 Vamos criar o seu perfil estilo Tinder!\n\nQual é o seu **Nome e Idade**? (Ex: Ana, 23 anos)")
    bot.register_next_step_handler(message, salvar_nome)

def salvar_nome(message):
    id_usuario = message.chat.id
    if id_usuario not in dados_cadastro: return
    dados_cadastro[id_usuario]['nome'] = message.text
    
    # Pergunta o Gênero com Botões Inline
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Homem 🧑", callback_data="gen_homem"),
        InlineKeyboardButton("Mulher 👩", callback_data="gen_mulher")
    )
    bot.send_message(id_usuario, "Qual é o seu gênero?", reply_markup=markup)

# Captura a resposta do Gênero e passa para "O que procura"
@bot.callback_query_handler(func=lambda call: call.data.startswith("gen_"))
def salvar_genero(call):
    id_usuario = call.message.chat.id
    if id_usuario not in dados_cadastro: return
    
    genero_escolhido = "Homem" if call.data == "gen_homem" else "Mulher"
    dados_cadastro[id_usuario]['genero'] = genero_escolhido
    
    bot.edit_message_reply_markup(id_usuario, call.message.message_id, reply_markup=None)
    
    # Pergunta o que procura com Botões Inline
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Homens 🧑", callback_data="proc_homem"),
        InlineKeyboardButton("Mulheres 👩", callback_data="proc_mulher"),
        InlineKeyboardButton("Ambos 🧑‍🤝‍🧑", callback_data="proc_ambos")
    )
    bot.send_message(id_usuario, "O que você está procurando no bot?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("proc_"))
def salvar_procura(call):
    id_usuario = call.message.chat.id
    if id_usuario not in dados_cadastro: return
    
    mapeamento = {"proc_homem": "Homem", "proc_mulher": "Mulher", "proc_ambos": "Ambos"}
    dados_cadastro[id_usuario]['procura'] = mapeamento[call.data]
    
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
            INSERT OR REPLACE INTO perfis (telegram_id, nome, bio, foto, genero, procura) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (id_usuario, dados_cadastro[id_usuario]['nome'], dados_cadastro[id_usuario]['bio'], id_foto, dados_cadastro[id_usuario]['genero'], dados_cadastro[id_usuario]['procura']))
        conn.commit()
        conn.close()
        bot.send_message(id_usuario, "🎉 Perfil criado! Digite `/tinder` para começar.", parse_mode="Markdown")
        del dados_cadastro[id_usuario]
    else:
        bot.send_message(id_usuario, "❌ Por favor, envie uma foto válida.")
        bot.register_next_step_handler(message, salvar_foto)

# ----------------- NOVO COMANDO: MOSTRAR SEU PERFIL -----------------

@bot.message_handler(commands=['perfil'])
def ver_meu_perfil(message):
    my_id = message.chat.id
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT nome, bio, foto, genero, procura FROM perfis WHERE telegram_id = ?", (my_id,))
    perfil = cursor.fetchone()
    conn.close()
    
    if perfil:
        nome, bio, foto, genero, procura = perfil
        bot.send_photo(
            my_id, foto, 
            caption=f"📝 **Seu Perfil Atual:**\n\n**Nome:** {nome}\n**Gênero:** {genero}\n**Procura por:** {procura}\n**Bio:** {bio}\n\nPara atualizar, basta digitar `/cadastro` de novo.",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(my_id, "⚠️ Você ainda não tem um perfil criado! Digite `/cadastro`.")

# ----------------- NOVO COMANDO: MOSTRAR MATCHS -----------------

@bot.message_handler(commands=['matches', 'matchs'])
def ver_meus_matches(message):
    my_id = message.chat.id
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Seleciona todos os usuários onde a curtida foi mútua
    cursor.execute('''
        SELECT p.nome, p.telegram_id FROM perfis p
        WHERE p.telegram_id IN (
            SELECT para_id FROM curtidas WHERE de_id = ?
        ) AND p.telegram_id IN (
            SELECT de_id FROM curtidas WHERE para_id = ?
        )
    ''', (my_id, my_id))
    
    lista_matches = cursor.fetchall()
    conn.close()
    
    if lista_matches:
        texto = "💌 **Seus Matches Atuais:**\n\n"
        for nome_match, id_match in lista_matches:
            # Tenta pegar o link direto, se não tiver username, mostra menção por ID
            texto += f"• **{nome_match}** - [Conversar no Privado](tg://user?id={id_match})\n"
        bot.send_message(my_id, texto, parse_mode="Markdown")
    else:
        bot.send_message(my_id, "💔 Você ainda não tem nenhum Match. Continue dando curtidas no `/tinder`!")

# ----------------- FLUXO DO TINDER COM FILTRO DE BUSCA -----------------

@bot.message_handler(commands=['start', 'tinder'])
def mostrar_proximo_perfil(message):
    my_id = message.chat.id
    conn = conectar_bd()
    cursor = conn.cursor()
    
    # Pega as preferências de quem está buscando
    cursor.execute("SELECT procura FROM perfis WHERE telegram_id = ?", (my_id,))
    resultado_busca = cursor.fetchone()
    
    if not resultado_busca:
        bot.send_message(my_id, "⚠️ Crie um perfil antes! Digite `/cadastro`.", parse_mode="Markdown")
        conn.close()
        return
        
    oq_procura = resultado_busca[0]
    
    # Monta o filtro SQL baseado no que a pessoa procura (Homem, Mulher ou Ambos)
    if oq_procura == "Ambos":
        query = '''
            SELECT telegram_id, nome, bio, foto FROM perfis 
            WHERE telegram_id != ? AND telegram_id NOT IN (SELECT para_id FROM curtidas WHERE de_id = ?) LIMIT 1
        '''
        parametros = (my_id, my_id)
    else:
        query = '''
            SELECT telegram_id, nome, bio, foto FROM perfis 
            WHERE telegram_id != ? AND genero = ? AND telegram_id NOT IN (SELECT para_id FROM curtidas WHERE de_id = ?) LIMIT 1
        '''
        parametros = (my_id, oq_procura, my_id)
        
    cursor.execute(query, parametros)
    perfil = cursor.fetchone()
    conn.close()
    
    if perfil:
        perfil_id, nome, bio, foto = perfil
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("❌ Próximo", callback_data=f"prox_{perfil_id}"), InlineKeyboardButton("❤️ Curtir", callback_data=f"curt_{perfil_id}"))
        bot.send_photo(my_id, foto, caption=f"**{nome}**\n\n{bio}", reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(my_id, "🌟 Você já viu todos os perfis compatíveis no momento!")

# ----------------- TRATAMENTO DOS BOTÕES (CALLBACK) -----------------

@bot.callback_query_handler(func=lambda call: call.data.startswith(("curt_", "prox_", "confirmar_", "cancelar_")))
def tratar_botoes(call):
    my_id = call.message.chat.id
    
    if call.data == "confirmar_deletar":
        bot.edit_message_reply_markup(my_id, call.message.message_id, reply_markup=None)
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM perfis WHERE telegram_id = ?", (my_id,))
        cursor.execute("DELETE FROM curtidas WHERE de_id = ? OR para_id = ?", (my_id, my_id))
        conn.commit()
        conn.close()
        bot.answer_callback_query(call.id, "Perfil deletado!", show_alert=True)
        bot.send_message(my_id, "❌ Perfil removido.")
        return
        
    elif call.data == "cancelar_deletar":
        bot.edit_message_reply_markup(my_id, call.message.message_id, reply_markup=None)
        bot.answer_callback_query(call.id, "Mantido! 😉")
        return
        
