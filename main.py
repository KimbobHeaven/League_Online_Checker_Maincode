import discord
from keep_running import keep_alive
import os
from dotenv import load_dotenv
import requests
import time

load_dotenv()
api_key = os.getenv('API_KEY')
token = os.getenv('DISCORD_TOKEN')
league_version = os.getenv('LEAGUE_VERSION')
# 변수들 로드


class MyClient(discord.Client):
    async def on_ready(self):
        print('\nLogged on as', self.user)
        # 디코 봇 온라인(로그인) 메세지

    async def on_message(self, message):
        if message.author == self.user:
            return
            # 해당 봇이 입력하는 메세지는 제외

        check_list = []
        f = open('./check_list.txt', 'r', encoding='UTF-8')
        while True:
            line = f.readline()
            check_list.append(line[:-1])
            if not line:
                break
        f.close()
        print(check_list)
        # 체크 계정 목록 로드

        champion_id_dict = requests.get(
            "http://ddragon.leagueoflegends.com/cdn/" + league_version + "/data/ko_KR/champion.json")
        champion_keys = champion_id_dict.json()['data'].keys()
        # 챔피언 id 로드

        game_queue_config_id_converter = {"420": "솔랭", "430": "일반", "440": "자랭", "450": "칼바람"}
        # 게임종류 로드

        if message.content == '!염탐':
            await message.channel.send('염탐중...')
            # 작업중 메시지 출력

            final_message = ""
            for s in range(len(check_list) - 1):
                summoner_name = check_list[s]
                print(summoner_name)
                summoner = "https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + summoner_name + '?api_key=' + api_key
                r1 = requests.get(summoner)
                summoner_id = r1.json()['id']
                spectator = "https://kr.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/" + summoner_id + '?api_key=' + api_key
                r2 = requests.get(spectator)
                # riot api에서 summoner id, spectator game 로드

                champion_name = ''
                if r2.status_code != 404:  # 게임을 돌리고 있는지 구분
                    if r2.json()['gameType'] == "MATCHED_GAME":
                        game_queue_config_id = r2.json()['gameQueueConfigId']
                        game_type = str(game_queue_config_id_converter[str(game_queue_config_id)])
                    else:
                        game_type = '사설'
                    # 게임 종류 파악

                    for i in range(10):
                        if r2.json()['participants'][i]['summonerName'] == summoner_name:
                            champion_id = r2.json()['participants'][i]['championId']
                            for c in champion_keys:
                                if champion_id == int(champion_id_dict.json()['data'][c]['key']):
                                    champion_name = champion_id_dict.json()['data'][c]['name']
                                    break
                    # 플레이중인 챔피언 찾기

                    gamelength_second = r2.json()['gameLength'] + 210
                    gamelength_minute = time.strftime('%M:%S', time.gmtime(gamelength_second))
                    # 플레이 시간 형태 변형

                    print(summoner_name + ' (' + game_type + ', ' + gamelength_minute + ') : ' + champion_name)
                    final_message = final_message + summoner_name + ' (' + game_type + ', ' + gamelength_minute + ') : ' + champion_name + '\n'
                    # 출력 메시지 저장

                else:  # 겜 안하면 패스
                    continue

            if final_message == "":  # 출력 메시지 저장개수 0
                await message.channel.send("다 롤 접었나?")
            else:
                await message.channel.send(final_message)
            final_message = ""  # 출력 메시지 리셋


client = MyClient()  # ?
keep_alive()  # 서버 24시간 구동
client.run(token)  # 디코 토큰
