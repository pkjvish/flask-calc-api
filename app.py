from flask import Flask, request, jsonify
from calculator import Calculator

app = Flask(__name__)
calc = Calculator()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "calc-api"}), 200


@app.route("/api/v1/add", methods=["POST"])
def add():
    data = request.get_json()
    return jsonify({"operation": "add", "a": data["a"], "b": data["b"],
                    "result": calc.add(data["a"], data["b"])})


@app.route("/api/v1/subtract", methods=["POST"])
def subtract():
    data = request.get_json()
    return jsonify({"operation": "subtract", "a": data["a"], "b": data["b"],
                    "result": calc.subtract(data["a"], data["b"])})


@app.route("/api/v1/multiply", methods=["POST"])
def multiply():
    data = request.get_json()
    return jsonify({"operation": "multiply", "a": data["a"], "b": data["b"],
                    "result": calc.multiply(data["a"], data["b"])})


@app.route("/api/v1/divide", methods=["POST"])
def divide():
    data = request.get_json()
    if data["b"] == 0:
        return jsonify({"error": "Division by zero is not allowed"}), 400
    return jsonify({"operation": "divide", "a": data["a"], "b": data["b"],
                    "result": calc.divide(data["a"], data["b"])})


@app.route("/api/v1/power", methods=["POST"])
def power():
    data = request.get_json()
    return jsonify({"operation": "power", "a": data["a"], "b": data["b"],
                    "result": calc.power(data["a"], data["b"])})


@app.route("/api/v1/sqrt", methods=["POST"])
def sqrt():
    data = request.get_json()
    if data["a"] < 0:
        return jsonify({"error": "Cannot compute square root of a negative number"}), 400
    return jsonify({"operation": "sqrt", "a": data["a"],
                    "result": calc.sqrt(data["a"])})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)