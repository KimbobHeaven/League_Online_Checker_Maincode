import discord
from keep_running import keep_alive
import os
from dotenv import load_dotenv
import requests
import time
import json

load_dotenv()
api_key = os.getenv('API_KEY')
token = os.getenv('DISCORD_TOKEN')
league_version = os.getenv('LEAGUE_VERSION')
# 변수들 로드

with open('./check_list.json', 'r', encoding='UTF-8') as json_file:
    check_list = json.load(json_file)
# 체크 계정 목록 로드

champion_id_dict = requests.get(
    "http://ddragon.leagueoflegends.com/cdn/" + league_version + "/data/ko_KR/champion.json")
champion_keys = champion_id_dict.json()['data'].keys()
# 챔피언 id 로드

game_queue_config_id_converter = {"420": "솔랭", "430": "일반", "440": "자랭", "450": "칼바람"}


# 게임종류 로드

class MyClient(discord.Client):
    async def on_ready(self):
        print('\nLogged on as', self.user)
        # 디코 봇 온라인(로그인) 메세지

    async def on_message(self, message):
        if message.author == self.user:
            return
            # 해당 봇이 입력하는 메세지는 제외

        with open('./check_list.json', 'r', encoding='UTF-8') as json_file:
            check_list = json.load(json_file)
            # 변경후 계정목록 재 로드

        def online_checker(summ_list):
            final_message = ''
            for s in summ_list:
                TF = bool
                for t in check_list.keys():
                    if s in check_list[t]:
                        TF = check_list[t][s]
                    else:
                        continue
                if len(summ_list) == 1:
                    TF = True

                if TF != False:  # True, bool
                    print('inspecting...' + s)
                    summ = s
                    summoner = "https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + summ + '?api_key=' + api_key
                    r1 = requests.get(summoner)
                    summoner_id = r1.json()['id']
                    spectator = "https://kr.api.riotgames.com/lol/spectator/v4/active-games/by-summoner/" + summoner_id + '?api_key=' + api_key
                    r2 = requests.get(spectator)
                    # riot api 에서 summoner id, spectator game 로드

                    if r2.status_code != 404:  # 게임 돌리는중
                        if r2.json()['gameType'] == "MATCHED_GAME":
                            game_queue_config_id = r2.json()['gameQueueConfigId']
                            game_type = str(game_queue_config_id_converter[str(game_queue_config_id)])
                        else:
                            game_type = '사설'
                        # 게임 종류 파악

                        champion_name = ''
                        for i in range(10):
                            if r2.json()['participants'][i]['summonerName'] == summ:
                                champion_id = r2.json()['participants'][i]['championId']
                                for s in champion_keys:
                                    if champion_id == int(champion_id_dict.json()['data'][s]['key']):
                                        champion_name = champion_id_dict.json()['data'][s]['name']
                                        break
                        # 플레이중인 챔피언 찾기

                        gamelength_second = r2.json()['gameLength'] + 210
                        gamelength_minute = time.strftime('%M:%S', time.gmtime(gamelength_second))
                        # 플레이 시간 형태 변형

                        final_message += final_message + summ + ' (' + game_type + ', ' + gamelength_minute + ') : ' + champion_name + '\n'
                        # 출력 메시지 저장

                    else:  # 겜 안하면 패스
                        continue
                else:  # False
                    continue
            return final_message

        def ligit_checker(summ_list):
            for i in range(len(summ_list)):
                summ = summ_list[i]
                summoner = "https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + summ + '?api_key=' + api_key
                r1 = requests.get(summoner)
                if r1.status_code == 200:  # 닉네임 존재
                    summ_list[i] = r1.json()["name"]  # 닉네임 correction
                    continue
                else:  # 닉네임 부존재
                    return False
            return summ_list

        def add(name, summ, all_name, all_summ):
            if summ in all_summ:  # summ in [summ]
                return '왜 있는사람을 추가하려하냐'
            else:  # summ not in [summ]
                if name not in all_name:
                    check_list[name] = dict()
                    # add new name dict

                check_list[name][summ] = True
                with open('./check_list.json', 'w', encoding='UTF-8') as out_file:
                    json.dump(check_list, out_file, indent='\t', ensure_ascii=False)
                return '추가했음'

        def remove(var, all_name, all_summ):
            if var in all_name:  # var 가 이름
                del (check_list[var])
                with open('./check_list.json', 'w', encoding='UTF-8') as out_file:
                    json.dump(check_list, out_file, indent='\t', ensure_ascii=False)
                return '지웠음'
            else:  # var 가 닉네임 or 아무것도 아님
                if var in all_summ:  # var 가 닉네임
                    for s in check_list.keys():
                        if var in check_list[s]:
                            if len(check_list[s].keys()) == 1:  # 닉네임 하나만 존재
                                del (check_list[s])
                            else:  # 닉네임 2개이상 존재
                                del (check_list[s][var])
                            with open('./check_list.json', 'w', encoding='UTF-8') as out_file:
                                json.dump(check_list, out_file, indent='\t', ensure_ascii=False)
                            return '지웠음'
                        else:
                            continue
                else:  # var 가 아무것도 아님
                    return '왜 없는사람을 지우려고하냐'

        def switch(summ_list, TF):
            for s in summ_list:
                for t in check_list.keys():
                    if s in check_list[t]:
                        check_list[t][s] = TF
                        break
            with open('./check_list.json', 'w', encoding='UTF-8') as out_file:
                json.dump(check_list, out_file, indent='\t', ensure_ascii=False)

        def switcher(factor, done_message, error_message, TF):
            all_name, all_summ = all_finder()
            if message.content == factor:
                switch(all_summ, TF)
                return done_message
            else:
                var = message.content[4:]
                if var in all_name:
                    switch(check_list[var].keys(), TF)
                    return done_message
                elif var in all_summ:
                    var_list = [var]
                    switch(var_list, TF)
                    return done_message
                else:
                    return error_message

        def all_finder():
            all_name = check_list.keys()
            all_summ = []
            for s in check_list.keys():
                for t in check_list[s]:
                    all_summ.append(t)
            return all_name, all_summ

        factor = message.content.split(' ', 2)
        # 명령어 인자 설정

        if factor[0] == '!염탐':
            await message.channel.send('염탐중...')
            # 작업중 메시지 출력

            all_name, all_summ = all_finder()
            summ_list = []
            if message.content == '!염탐':  # !염탐
                for s in check_list.keys():  # summ_list 설정
                    for t in check_list[s]:
                        summ_list.append(t)

                final_message = online_checker(summ_list)
                if final_message == "":  # 출력 메시지 저장개수 0
                    await message.channel.send("다 롤 접은듯")
                else:  # 1명이상 게임중
                    await message.channel.send(final_message)

            elif message.content[4:] in check_list.keys():  # !염탐 [이름]
                for t in check_list[message.content[4:]]:
                    summ_list.append(t)

                final_message = online_checker(summ_list)
                if final_message == "":  # 출력 메시지 저장개수 0
                    await message.channel.send("얘 롤 접은듯")
                else:  # 1계정이상 게임중
                    await message.channel.send(final_message)

            else:  # !염탐 [닉네임]
                summ_list.append(message.content[4:])
                summ_list = ligit_checker(summ_list)
                if summ_list != False:  # ligit
                    final_message = online_checker(summ_list)
                    if final_message == "":  # 출력 메시지 저장개수 0
                        await message.channel.send("얘 롤 접은듯")
                    else:  # 게임중
                        await message.channel.send(final_message)
                else:  # none ligit
                    await message.channel.send("왜 없는사람을 찾냐")

        if message.content == '!목록':
            check_list_output = ''
            for s in check_list.keys():
                check_list_output += '<' + s + '>' + '\n'
                for t in check_list[s]:
                    check_list_output += t
                    check_list_output += ' : ' + str(check_list[s][t]) + '\n'
            await message.channel.send(check_list_output)

        if factor[0] == '!추가':
            if len(factor) != 3:  # 형식 불일치
                await message.channel.send('형식 맞춰라;;\n!추가 [이름] [닉네임]')
            else:  # 형식 일치
                name = factor[1]
                summ = ['']
                summ[0] = str(factor[2])
                summ = ligit_checker(summ)

                if summ != False:  # ligit
                    all_name, all_summ = all_finder()
                    await message.channel.send(add(name, summ[0], all_name, all_summ))
                else:  # none ligit
                    await message.channel.send('왜 없는사람을 추가하려하냐')

        if factor[0] == '!제거':
            var = message.content[4:]
            all_name, all_summ = all_finder()
            await message.channel.send(remove(var, all_name, all_summ))

        if factor[0] == '!변경':
            new_factor = message.content[4:].split(',', 1)
            if len(new_factor) != 2:  # 형식 diff
                await message.channel.send('형식 맞춰라;;\n!변경 [전닉네임] , [후닉네임]')
            else:  # 형식 correct
                summ_list = [new_factor[0], new_factor[1]]
                summ_list = ligit_checker(summ_list)
                if summ_list != False:  # ligit
                    summ1 = summ_list[0]
                    summ2 = summ_list[1]
                    all_name, all_summ = all_finder()
                    if summ1 in all_summ:  # summ1 in [summ]
                        if summ1 == summ2:  # summ1 summ2 same
                            await message.channel.send('그렇게 시킬게 없냐?')
                        else:  # summ1 summ2 diff
                            if summ2 in all_summ:  # summ2 in [summ]
                                await message.channel.send('이미 있는데 뭐함?')
                            else:  # all ready
                                for s in check_list.keys():
                                    if summ1 in check_list[s]:
                                        status_summ1 = check_list[s][summ1]
                                        add(s, summ2, all_name, all_summ)
                                        remove(summ1, all_name, all_summ)
                                        check_list[s][summ2] = status_summ1
                                        with open('./check_list.json', 'w', encoding='UTF-8') as out_file:
                                            json.dump(check_list, out_file, indent='\t', ensure_ascii=False)
                                        await message.channel.send('바궜음')
                                        break
                    else:  # summ1 not in [summ]
                        await message.channel.send('닉좀 잘쓰자?')
                else:  # none ligit
                    await message.channel.send('닉좀 잘쓰자?')

        if factor[0] == '!켜기':
            await message.channel.send(switcher('!켜기', '다켰음', '잘 좀 쓰자?', True))
            # all_name, all_summ = all_finder()
            # if message.content == '!켜기':
            #     switch(all_summ, True)
            #     await message.channel.send('켰음')
            # else:
            #     var = message.content[4:]
            #     if var in all_name:
            #         switch(check_list[var].keys(), True)
            #         await message.channel.send('켰음')
            #     elif var in all_summ:
            #         var_list = [var]
            #         switch(var_list, True)
            #         await message.channel.send('켰음')
            #     else:
            #         await message.channel.send('잘 좀 쓰자?')

        if factor[0] == '!끄기':
            await message.channel.send(switcher('!끄기', '다껐음', '잘 좀 쓰자?', False))
            # all_name, all_summ = all_finder()
            # if message.content == '!끄기':
            #     switch(all_summ, False)
            #     await message.channel.send('껐음')
            # else:
            #     var = message.content[4:]
            #     if var in all_name:
            #         switch(check_list[var].keys(), False)
            #         await message.channel.send('껐음')
            #     elif var in all_summ:
            #         var_list = [var]
            #         switch(var, False)
            #         await message.channel.send('껐음')
            #     else:
            #         await message.channel.send('잘 좀 쓰자?')

        if message.content == '!도움':
            await message.author.send(
                """
염탐
: 목록에 있는 계정들의 현황 체크
염탐 [이름]
: 해당 사람의 계정들의 현황 체크
염탐 [닉네임]
: 해당 닉네임의 현황 체크
ㅡㅡㅡㅡㅡ
목록
: 체크할 계정들의 목록 나열
ㅡㅡㅡㅡㅡ
추가 [이름] [닉네임]
: 해당 사람의 계정으로 목록에 추가
ㅡㅡㅡㅡㅡ
제거 [이름]
: 해당 사람의 모든 계정을 제거
제거 [닉네임]
: 해당 닉네임을 목록에서 제거
ㅡㅡㅡㅡㅡ
변경 [전 닉네임] , [후 닉네임]
: [전 닉네임]을 [후 닉네임]으로 변경
ㅡㅡㅡㅡㅡ
켜기/끄기 전체
: 모든 계정의 체크여부를 변경
켜기/끄기 [이름]
: 해당 사람의 체크여부를 변경
켜기/끄기 [닉네임]
: 해당 계정의 체크여부를 변경
ㅡㅡㅡㅡㅡ
도움
: 모든 사용법 나열
""")


client = MyClient()  # ?
keep_alive()  # 서버 24시간 구동
client.run(token)  # 디코 토큰
