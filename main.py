import requests
from bs4 import BeautifulSoup
import time
import re
import pandas as pd

# 공통 헤더 설정
def get_common_headers():
    # HTTP 요청에 사용될 공통 헤더를 반환합니다.
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

# 앨범 ID 추출
def extract_album_id(soup):
    # BeautifulSoup 객체에서 앨범 ID를 추출합니다.
    elems = soup.select('div.info-zone span.value > a')
    for elem in elems:
        onclick_attr = elem.get('onclick') if elem else None
        result = re.search(r"fnGoMore\('albumInfo','(\d+)'\)", onclick_attr) if onclick_attr else None
        if result:
            return result.group(1)
    return None

# 앨범 ID 가져오기
def get_album_id(url, headers):
    # 주어진 URL에서 앨범 ID를 가져옵니다.
    response = requests.get(url, allow_redirects=True, timeout=3, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    return extract_album_id(soup)

# 노래 목록 추출
def extract_song_list(soup):
    # BeautifulSoup 객체에서 노래 목록을 추출합니다.
    song_list = []
    for elem in soup.select('td.info > a.title'):
        song_list.append(elem.attrs['title'])
    return song_list

# 앨범 정보 추출
def extract_album_info(soup):
    # BeautifulSoup 객체에서 앨범 정보를 추출합니다.
    album_info = {}

    # h2 태그에서 앨범 제목을 추출합니다.
    title_elem = soup.select_one('h2.name')
    if title_elem:
        album_info['Title'] = title_elem.text.strip()

    # ul.info-data에서 첫 번째 li 요소의 span.value를 찾아 아티스트 이름을 추출합니다.
    artist_elem = soup.select_one('ul.info-data li:first-child span.value')
    if artist_elem:
        album_info['Artist'] = artist_elem.text.strip()

    return album_info

# 앨범 정보 가져오기
def get_album_info(album_id, headers):
    # 앨범 ID를 사용하여 앨범 정보를 가져옵니다.
    response = requests.get(f'https://www.genie.co.kr/detail/albumInfo?axnm={album_id}', headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    return extract_album_info(soup)

# 노래 목록 가져오기
def get_song_list(album_id, headers):
    # 앨범 ID를 사용하여 노래 목록을 가져옵니다.
    response = requests.get(f'https://www.genie.co.kr/detail/albumInfo?axnm={album_id}', headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    return extract_song_list(soup)

# 엑셀 파일로 내보내기
def export_to_excel(album_data, filename):
    # 앨범 데이터를 엑셀 파일로 내보내되, 노래 목록의 각 요소와 앨범 정보를 새로운 행으로 저장합니다.
    rows = []
    for album in album_data:
        album_info = get_album_info(album['Album ID'], get_common_headers())  # 앨범 정보를 가져옵니다.
        for song in album['Song List']:
            row = {
                'Album Number': album['Album Number'],
                'Artist': album_info.get('Artist', ''),
                'Album Title': album_info.get('Title', ''),
                'Song Name': song
            }
            rows.append(row)
    df = pd.DataFrame(rows)
    df.to_excel(filename, index=False)
    print(f'Exported to {filename}')

# 텍스트 파일로 내보내기
def export_to_text(album_data, filename):
    # 앨범 데이터를 텍스트 파일로 내보내되, 각 노래를 '[artist name] - [song name]' 형식으로 저장합니다.
    with open(filename, 'w', encoding='utf-8') as file:
        for album in album_data:
            album_info = get_album_info(album['Album ID'], get_common_headers())  # 앨범 정보를 가져옵니다.
            for song in album['Song List']:
                file.write(f"{album_info.get('Artist', '')} - {song}\n")
    print(f'Exported to {filename}')

# 메인 함수
def main():
    headers = get_common_headers()
    base_url = 'https://www.ebs.co.kr/space/bestalbum/albumView/{}'
    album_data = []

    for number in range(1, 101):
        url = base_url.format(number)
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        data_link_element = soup.select_one('#Container > div.sub_conts > div > div > div.summary > div.btn_wrap.viewbtn > a')
        
        if data_link_element and 'data-link' in data_link_element.attrs:
            data_link = data_link_element['data-link']
            print(f'URL for album {number}: {data_link}')
            if data_link.startswith('https://www.genie.co.kr/'):
                album_id = get_album_id(data_link, headers)
                song_list = get_song_list(album_id, headers)
                album_data.append({'Album Number': number, 'Album ID': album_id, 'Song List': song_list})
                print(album_id)
                print(song_list)
        else:
            print(f'Data-link not found for album {number}')
    
    # 엑셀 파일로 데이터 내보내기
    export_to_excel(album_data, 'album_data.xlsx')
    
    # 텍스트 파일로 데이터 내보내기
    export_to_text(album_data, 'album_data.txt')

if __name__ == '__main__':
    main()