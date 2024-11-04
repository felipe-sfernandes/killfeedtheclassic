import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Configuração do Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("cred.json", scope)
client_gspread = gspread.authorize(creds)
sheet = client_gspread.open("Kda The Classic")

# Verificar se a aba já existe
data_hoje = datetime.now().strftime('%Y-%m-%d')
try:
    nova_aba = sheet.add_worksheet(title=data_hoje, rows="1000", cols="5")  # Atualizado para 5 colunas
    nova_aba.append_row(['hora', 'clan', 'nick', 'Kills', 'Deaths'])  # Adicionando a coluna 'hora'
except gspread.exceptions.APIError as e:
    if "already exists" in str(e):
        nova_aba = sheet.worksheet(data_hoje)
    else:
        raise e

# Iniciar o dataframe
df = pd.DataFrame(columns=['hora', 'clan', 'nick', 'Kills', 'Deaths'])  # Incluindo a coluna 'hora'

# Função para processar o conteúdo do arquivo
def processar_kf_txt():
    with open('kf.txt', 'r', encoding='utf-8') as file:
        lines = file.readlines()
        
        for line in lines:
            if ":crossed_swords:" in line:
                print(f"Processando linha: {line.strip()}")
                time = line.split()[1]  # Extraindo a hora
                parts = line.split(" matou ")
                attacker_part = parts[0]
                victim_part = parts[1]
                
                attacker_clan, attacker_nick = extract_clan_and_nick(attacker_part)
                killed_clan, killed_nick = extract_clan_and_nick(victim_part)

                print(f"Extraído - Hora: {time}, Atacante: {attacker_clan}, {attacker_nick}; Vítima: {killed_clan}, {killed_nick}")
                
                if attacker_clan and attacker_nick and killed_clan and killed_nick:
                    global df
                    df = update_dataframe(df, time, attacker_clan, attacker_nick, killed_clan, killed_nick)
        
        # Depuração: imprimir o DataFrame antes de enviar para o Google Sheets
        print("DataFrame final:")
        print(df)

        # Atualizar a aba existente com o DataFrame
        nova_aba.clear()
        nova_aba.append_row(df.columns.values.tolist())
        nova_aba.append_rows(df.values.tolist())

def extract_clan_and_nick(part):
    """
    Extrai o nome do clã e o nick do jogador de uma parte da mensagem.
    """
    clan_start = part.find("[")
    clan_end = part.find("]")
    clan_name = part[clan_start+1:clan_end].strip()
    
    nick_start = clan_end + 1
    nick_name = part[nick_start:].strip()

    return clan_name, nick_name

def update_dataframe(df, time, attacker_clan, attacker_nick, killed_clan, killed_nick):
    # Atualiza Kills do atacante
    if attacker_nick in df['nick'].values:
        df.loc[df['nick'] == attacker_nick, 'Kills'] += 1
    else:
        df = pd.concat([df, pd.DataFrame([{'hora': time, 'clan': attacker_clan, 'nick': attacker_nick, 'Kills': 1, 'Deaths': 0}])], ignore_index=True)

    # Atualiza Deaths da vítima
    if killed_nick in df['nick'].values:
        df.loc[df['nick'] == killed_nick, 'Deaths'] += 1
    else:
        df = pd.concat([df, pd.DataFrame([{'hora': time, 'clan': killed_clan, 'nick': killed_nick, 'Kills': 0, 'Deaths': 1}])], ignore_index=True)

    return df

# Processar o arquivo kf.txt
processar_kf_txt()
