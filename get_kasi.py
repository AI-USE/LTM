from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route("/")
def home():
    return "歌詞スクレイピングAPI（学習用）"

@app.route("/scrape", methods=["GET"])
def scrape():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "url パラメータを指定してください"}), 400

    try:
        res = requests.get(url, timeout=10)
        res.encoding = res.apparent_encoding
        html = res.text
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")

    if not title_tag:
        return jsonify({"error": "タイトルが取得できません"}), 500

    full_title = title_tag.text.strip()

    # パターンチェック
    if "歌詞" in full_title and "ふりがな付" in full_title and "うたてん" in full_title:
        try:
            # 曲名 = "歌詞" の前
            song = full_title.split("歌詞")[0].strip()

            # 作者 = "ふりがな付" の前から直前の部分を抜き出す
            author = full_title.split("歌詞")[1].split("ふりがな付")[0].strip()

            return jsonify({
                "song": song,
                "author": author,
                "title_raw": full_title
            })
        except Exception as e:
            return jsonify({"error": f"解析に失敗しました: {str(e)}"}), 500
    else:
        return jsonify({"error": "対応していないタイトル形式です"}), 400

if __name__ == "__main__":
    app.run()
