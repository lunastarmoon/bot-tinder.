import os
import sqlite3
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- CORREÇÃO OBRIGATÓRIA PARA OS ERROS DO RENDER ---
class ServidorFalso(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot Tinder Online!")

def rodar_servidor_falso():
    # Puxa a porta padrão que o Render exige automaticamente
    porta = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', porta), ServidorFalso)
    server.serve_forever()

# Abre o canal de comunicação para sumir com os logs vermelhos do fim
threading.Thread(target=rodar_servidor_falso, daemon=True).start()

# --- INSTÂNCIA DO BOT TELEGRAM ---
API_TOKEN = '8733102844:AAEpegvJAW62cnAOeP-iphHSnKhCqe257dz4'
bot = telebot.TeleBot(API_TOKEN)
dados_cadastro = {}


def iniciar_bd():
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS perfis (
            telegram_id INTEGER PRIMARY KEY, nome TEXT, bio TEXT, foto TEXT
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
    bot.send_message(id_usuario, "Ótimo! Agora digite uma **Bio** curta falando sobre você:")
    bot.register_next_step_handler(message, salvar_bio)

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
        cursor.execute('INSERT OR REPLACE INTO perfis VALUES (?, ?, ?, ?)', (id_usuario, dados_cadastro[id_usuario]['nome'], dados_cadastro[id_usuario]['bio'], id_foto))
        conn.commit()
        conn.close()
        bot.send_message(id_usuario, "🎉 Perfil criado! Digite `/tinder` para começar.", parse_mode="Markdown")
        del dados_cadastro[id_usuario]
    else:
        bot.send_message(id_usuario, "❌ Por favor, envie uma foto válida.")
        bot.register_next_step_handler(message, salvar_foto)

@bot.message_handler(commands=['sair', 'deletar'])
def confirmar_saida(message):
    id_usuario = message.chat.id
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("✅ Sim, apagar tudo", callback_data="confirmar_deletar"), InlineKeyboardButton("❌ Não, continuar", callback_data="cancelar_deletar"))
    bot.send_message(id_usuario, "⚠️ Tem certeza que deseja apagar seu perfil?", reply_markup=markup)

@bot.message_handler(commands=['start', 'tinder'])
def mostrar_proximo_perfil(message):
    my_id = message.chat.id
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM perfis WHERE telegram_id = ?", (my_id,))
    if not cursor.fetchone():
        bot.send_message(my_id, "⚠️ Crie um perfil antes! Digite `/cadastro`.", parse_mode="Markdown")
        conn.close()
        return
    cursor.execute('SELECT telegram_id, nome, bio, foto FROM perfis WHERE telegram_id != ? AND telegram_id NOT IN (SELECT para_id FROM curtidas WHERE de_id = ?) LIMIT 1', (my_id, my_id))
    perfil = cursor.fetchone()
    conn.close()
    if perfil:
        perfil_id, nome, bio, foto = perfil
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("❌ Próximo", callback_data=f"proximo_{perfil_id}"), InlineKeyboardButton("❤️ Curtir", callback_data=f"curtir_{perfil_id}"))
        bot.send_photo(my_id, foto, caption=f"**{nome}**\n\n{bio}", reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(my_id, "🌟 Você já viu todos os perfis cadastrados no momento!")

@bot.callback_query_handler(func=lambda call: True)
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
    elif call.data.startswith("curtir_"):
        alvo_id = int(call.data.split("_")[1])
        conn = conectar_bd()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO curtidas VALUES (?, ?)", (my_id, alvo_id))
            conn.commit()
        except sqlite3.IntegrityError: pass
        cursor.execute("SELECT 1 FROM curtidas WHERE de_id = ? AND para_id = ?", (alvo_id, my_id))
        match_existe = cursor.fetchone()
        cursor.execute("SELECT nome FROM perfis WHERE telegram_id = ?", (my_id,))
        resultado_nome = cursor.fetchone()
        meu_nome = resultado_nome[0] if resultado_nome else "Alguém"
        conn.close()
        bot.edit_message_reply_markup(my_id, call.message.message_id, reply_markup=None)
        if match_existe:
            bot.answer_callback_query(call.id, "É UM MATCH! 😍", show_alert=True)
            bot.send_message(my_id, "🎉 **MATCH!** Vocês se curtiram mutuamente!")
            try:
                username = f"@{call.from_user.username}" if call.from_user.username else "este usuário"
                bot.send_message(alvo_id, f"🎉 **MATCH!** O perfil **{meu_nome}** te curtiu de volta! Converse aqui: {username}")
            except Exception: pass
        else:
            bot.answer_callback_query(call.id, "Você curtiu o perfil!")
        mostrar_proximo_perfil(call.message)
    elif call.data.startswith("proximo_"):
        bot.edit_message_reply_markup(my_id, call.message.message_id, reply_markup=None)
        bot.answer_callback_query(call.id, "Próximo...")
        mostrar_proximo_perfil(call.message)

bot.infinity_polling()
