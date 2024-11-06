from flask import Flask, jsonify, request

from bot import AIBot, chroma_collection

app = Flask(__name__)

bot = AIBot()

@app.route("/data", methods=["GET"])
def get_all_data():
    results = chroma_collection.query(query_texts=[""], n_results=100)  # Retorna as 100 primeiras entradas
    return jsonify(results)


@app.route("/", methods=["POST"])
def get_response():
    data = request.json
    question = data.get("question")
 
    answer = bot.invoke(question)
    print(answer)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

