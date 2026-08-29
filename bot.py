import json
import os
from datetime import datetime
from collections import defaultdict
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

TOKEN = "8983698534:AAHwbxjzA4NvjhvQlvg-Lt-CnYX3XCN9e_s"
DATA_FILE = "data.json"

CATEGORIES = ["🍔 Oziq-ovqat","🚗 Transport","🏠 Uy-joy","🛍 Xaridlar","☕ Kafe","💊 Sog'liq","📱 Aloqa","📚 Ta'lim","💳 Kredit","📦 Boshqa"]

def load_data():
    if not os.path.exists(DATA_FILE): return []
    try:
        with open(DATA_FILE,'r',encoding='utf-8') as f: return json.load(f)
    except: return []

def save_data(d):
    with open(DATA_FILE,'w',encoding='utf-8') as f:
        json.dump(d,f,ensure_ascii=False,indent=2)

def menu():
    return ReplyKeyboardMarkup([
        ["💰 Kirim","💸 Xarajat"],
        ["📊 Hisobot","📜 Tarix"],
        ["🗑 O'chirish"]], resize_keyboard=True)

async def start(u:Update,c):
    c.user_data.clear()
    await u.message.reply_text("💵 Finance Bot\nKerakli bo'limni tanlang.",reply_markup=menu())

async def income(u,c):
    c.user_data['mode']='income'
    await u.message.reply_text("Summa va izoh:\nMisol: 5000000 Maosh")

async def expense(u,c):
    kb=[[x] for x in CATEGORIES]
    await u.message.reply_text("Kategoriyani tanlang",reply_markup=ReplyKeyboardMarkup(kb,resize_keyboard=True))
    c.user_data['mode']='pick'

async def save_tx(u,c):
    t=u.message.text.strip(); mode=c.user_data.get('mode')
    if mode=='pick' and t in CATEGORIES:
        c.user_data['category']=t; c.user_data['mode']='expense'
        return await u.message.reply_text(f"{t}\n\nSumma va izoh yozing:\n150000 supermarket")
    if mode not in ['income','expense']: return
    p=t.split(maxsplit=1)
    if len(p)<2: return await u.message.reply_text("Misol: 150000 supermarket")
    amt=float(p[0].replace(',','').replace('.','').replace(' ','')); desc=p[1]
    d=load_data(); d.append({'user_id':u.effective_user.id,'type':mode,'amount':amt,'description':desc,'category':c.user_data.get('category','💰 Kirim'),'date':datetime.now().strftime('%Y-%m-%d %H:%M:%S')}); save_data(d)
    txt='💰 Kirim saqlandi' if mode=='income' else f"✅ {c.user_data['category']} saqlandi"
    c.user_data.clear(); await u.message.reply_text(f"{txt}\n\n{amt:,.0f} so'm\n📝 {desc}",reply_markup=menu())

async def report(u,c):
    d=load_data(); uid=u.effective_user.id; m=datetime.now().strftime('%Y-%m')
    rows=[x for x in d if x['user_id']==uid and x['date'].startswith(m)]
    inc=sum(x['amount'] for x in rows if x['type']=='income'); exp=sum(x['amount'] for x in rows if x['type']=='expense')
    bal=inc-exp; cat=defaultdict(float)
    for x in rows:
        if x['type']=='expense': cat[x['category']]+=x['amount']
    txt=f"📊 OYLIK HISOBOT\n📅 {m}\n\n💰 Kirim: {inc:,.0f}\n💸 Xarajat: {exp:,.0f}\n💵 Qoldiq: {bal:,.0f}\n\n📋 KATEGORIYALAR\n"
    if cat:
        top=max(cat,key=cat.get)
        for k,v in sorted(cat.items(),key=lambda i:i[1],reverse=True): txt+=f"{k}: {v:,.0f}\n"
        txt+=f"\n🏆 Eng ko'p: {top} ({cat[top]:,.0f})"
    else: txt+="Xarajat yo'q"
    await u.message.reply_text(txt,reply_markup=menu())

async def history(u,c):
    d=[x for x in load_data() if x['user_id']==u.effective_user.id][-10:]
    if not d: return await u.message.reply_text("Tarix bo'sh",reply_markup=menu())
    txt='📜 Oxirgi 10 ta\n\n'
    for x in reversed(d):
        s='+' if x['type']=='income' else '-'; e='💰' if x['type']=='income' else x['category']
        txt+=f"{e}\n{s}{x['amount']:,.0f} so'm\n{x['description']}\n{x['date']}\n\n"
    await u.message.reply_text(txt,reply_markup=menu())

async def delete_last(u,c):
    d=[x for x in load_data() if x['user_id']==u.effective_user.id]
    if not d: return await u.message.reply_text("O'chirish uchun yozuv yo'q",reply_markup=menu())
    x=d[-1]; kb=InlineKeyboardMarkup([[InlineKeyboardButton('✅ Ha',callback_data='yes'),InlineKeyboardButton('❌ Yo\'q',callback_data='no')]])
    await u.message.reply_text(f"O'chirish?\n\n{x['amount']:,.0f} so'm\n{x['description']}",reply_markup=kb)

async def callback(u,c):
    q=u.callback_query; await q.answer()
    if q.data=='no': return await q.edit_message_text("Bekor qilindi")
    d=load_data(); uid=q.from_user.id
    idx=max(i for i,v in enumerate(d) if v['user_id']==uid); x=d.pop(idx); save_data(d)
    await q.edit_message_text(f"✅ O'chirildi\n{x['amount']:,.0f} so'm")

async def msg(u,c):
    t=u.message.text
    if t=='💰 Kirim': return await income(u,c)
    if t=='💸 Xarajat': return await expense(u,c)
    if t=='📊 Hisobot': return await report(u,c)
    if t=='📜 Tarix': return await history(u,c)
    if t=="🗑 O'chirish": return await delete_last(u,c)
    if c.user_data.get('mode') in ['income','expense','pick']: return await save_tx(u,c)
    await u.message.reply_text("/start bosing",reply_markup=menu())

app=Application.builder().token(TOKEN).build(); app.add_handler(CommandHandler('start',start)); app.add_handler(CallbackQueryHandler(callback)); app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,msg)); print('BOT ISHGA TUSHDI'); app.run_polling()