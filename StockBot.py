import mysql.connector
import os
import discord
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

client = discord.Client()

mydb = mysql.connector.connect(
    host = 'localhost',
    user = 'root',
    password = 'Kimadam9697am',
    port = 3306,
    database = 'STOCKDB'
)

mycursor = mydb.cursor()

def getStock(stock_name):
    result = requests.get('https://finance.yahoo.com/quote/'+stock_name)
    src = result.content
    soup = BeautifulSoup(src, features='html.parser')

    scrape = soup.find("span",{'class':'Mb(-4px)'})
    return float(scrape.text.replace(',', ''))

def establish(user_id,guild_id):
    if(exists(user_id,guild_id)):
        return False
    else:
        sql = "INSERT INTO CAPITAL VALUES(%s,%s,10000)"
        args = [user_id,guild_id]
        mycursor.execute(sql,args)
        mydb.commit()
        return True

def getAmount(user_id,guild_id,stock_name):
    sql = 'SELECT COUNT(*) FROM STOCK WHERE USER_ID=%s AND GUILD_ID=%s AND STOCK_NAME=%s'
    args = [user_id,guild_id,stock_name]
    mycursor.execute(sql,args)
    return( mycursor.fetchall()[0][0] )

def getCapital(user_id,guild_id):
    sql = 'SELECT CAPITAL FROM CAPITAL WHERE USER_ID=%s AND GUILD_ID=%s'
    args = [user_id, guild_id]
    mycursor.execute(sql, args)
    return (mycursor.fetchall()[0][0])

def invest(user_id,guild_id,stock_name,amt):
    if(amt<1 or amt>100):
        return False
    if(getCapital(user_id,guild_id)<amt*getStock(stock_name)):
        print('Insufficient funds!')
        return False

    sql1 = "UPDATE CAPITAL SET CAPITAL = CAPITAL - %s WHERE USER_ID = %s AND GUILD_ID=%s"
    args1 = [getStock(stock_name)*amt,user_id,guild_id]
    mycursor.execute(sql1,args1)
    for i in range(amt):
        sql2 = "INSERT INTO STOCK VALUES(%s,%s,%s)"
        args2 = [user_id,guild_id,stock_name]
        mycursor.execute(sql2,args2)
    mydb.commit()
    return True

def sell(user_id,guild_id,stock_name,amt):
    if(amt<1):
        return False
    if(getAmount(user_id,guild_id,stock_name)<amt):
        print('Insufficient stock!')
        return False
    sql1 = "DELETE FROM STOCK WHERE USER_ID=%s AND GUILD_ID=%s AND STOCK_NAME=%s LIMIT %s"
    args1 = [user_id,guild_id,stock_name,amt]
    sql2 = "UPDATE CAPITAL SET CAPITAL = CAPITAL + %s WHERE USER_ID=%s AND GUILD_ID=%s"
    args2 = [getStock(stock_name)*amt,user_id,guild_id]
    mycursor.execute(sql1, args1)
    mycursor.execute(sql2,args2)
    mydb.commit()
    return True

def truncate():
    sql1 = "TRUNCATE TABLE STOCK"
    sql2 = "TRUNCATE TABLE CAPITAL"
    mycursor.execute(sql1)
    mycursor.execute(sql2)
    mydb.commit()

def portfolio(user_id,guild_id):
    sql1 = "SELECT * FROM STOCK WHERE USER_ID=%s  AND GUILD_ID=%s"
    args1 = [user_id,guild_id]
    mycursor.execute(sql1,args1)
    query1 = mycursor.fetchall()

    stocks = {}
    for stock in query1:
        if stock[2] in stocks:
            stocks[stock[2]]=stocks[stock[2]]+1
        else:
            stocks[stock[2]]=1
    return stocks

def exists(user_id,guild_id):
    sql = "SELECT COUNT(*) FROM CAPITAL WHERE USER_ID=%s AND GUILD_ID=%s"
    args = [user_id,guild_id]
    mycursor.execute(sql,args)
    if(mycursor.fetchall()[0][0]==0):
        return False
    else:
        return True

def net(user_id,guild_id):
    stocks = portfolio(user_id,guild_id)
    capital = getCapital(user_id,guild_id)
    sigma = capital
    for stock in stocks:
        sigma += stocks[stock]*getStock(stock)
    return sigma


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.channel.name != 'stocks':
        return
    try:
        args = message.content.split()
        if message.content.startswith('$get'):
            stock_name = args[1].upper()
            await message.channel.send('The current stock price of '+stock_name+' is $'+str(getStock(stock_name))+'.')
        elif message.content.startswith('$establish'):
            if(establish(message.author.id,message.guild.id)):
                await message.channel.send('Welcome to the market, '+message.author.name+'!')
            else:
                await message.channel.send('Account already exists!')
        elif message.content.startswith('$invest'):
            stock_name = args[1].upper()
            amt = int(args[2])
            if(invest(str(message.author.id),str(message.guild.id),stock_name,amt)):
                await message.channel.send(message.author.name + ' bought ' + str(amt) + ' stocks in ' + stock_name + '!')
            else:
                await message.channel.send('Insufficient funds!')
        elif message.content.startswith('$sell'):
            stock_name = args[1].upper()
            amt = int(args[2])
            if(sell(str(message.author.id),str(message.guild.id),stock_name,amt)):
                await message.channel.send(message.author.name + ' sold ' + str(amt) + ' stocks in ' + stock_name + '!')
            else:
                await message.channel.send('Insufficient stock!')
        elif message.content.startswith('$capital'):
            bal = getCapital(str(message.author.id),str(message.guild.id))
            await message.channel.send(message.author.name+'\'s capital is $'+str(bal))
        elif message.content.startswith('$portfolio'):
            await message.channel.send(message.author.name+'\'s portfolio: '+str(portfolio(str(message.author.id),str(message.guild.id))))
        elif message.content.startswith('$net'):
            await message.channel.send(message.author.name+'\'s net worth is $'+str(net(message.author.id,message.guild.id)))
        elif message.content.startswith('$graph'):
            stock_name = args[1].upper()
            await message.channel.send('https://finance.yahoo.com/chart/'+stock_name)
        else:
            return
    except:
        await message.channel.send('Uh oh, something went wrong.')


client.run(TOKEN)