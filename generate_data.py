import csv
import random
import string

# Define constants for realistic fake data
BRANDS_MODELS = {
    "Chevrolet": ["Onix", "Tracker", "Cruze", "Spin", "S10", "Equinox"],
    "Fiat": ["Argo", "Cronos", "Toro", "Pulse", "Fastback", "Mobi", "Strada"],
    "Volkswagen": ["Polo", "T-Cross", "Nivus", "Virtus", "Saveiro", "Taos"],
    "Toyota": ["Corolla", "Hilux", "Yaris", "Corolla Cross", "SW4"],
    "Ford": ["Ranger", "Territory", "Bronco", "Maverick"]
}

COLORS = ["Branco", "Preto", "Prata", "Cinza", "Vermelho", "Azul", "Bronze"]
STATUSES = ["Disponível", "Reservado", "Vendido"]

def generate_plate():
    # Mercosul format: ABC1D23
    letters1 = "".join(random.choices(string.ascii_uppercase, k=3))
    num1 = str(random.randint(0, 9))
    letter2 = random.choice(string.ascii_uppercase)
    num2 = "".join(random.choices(string.digits, k=2))
    return f"{letters1}{num1}{letter2}{num2}"

def generate_chassi():
    # 17 characters VIN (excluding I, O, Q to avoid confusion)
    chars = [c for c in string.ascii_uppercase + string.digits if c not in ("I", "O", "Q")]
    return "".join(random.choices(chars, k=17))

def main():
    random.seed(42) # For reproducibility
    vehicles = []
    
    for _ in range(100):
        brand = random.choice(list(BRANDS_MODELS.keys()))
        model = random.choice(BRANDS_MODELS[brand])
        plate = generate_plate()
        chassi = generate_chassi()
        year = random.randint(2015, 2026)
        
        # Price dependent somewhat on brand/model tier
        base_price = 50000
        if brand in ["Toyota", "Ford"] or model in ["Toro", "Cruze", "S10", "SW4", "T-Cross", "Taos"]:
            base_price = 120000
        
        price = base_price + random.randint(-15000, 150000)
        # Round to nearest thousand for cleaner look
        price = round(price / 1000) * 1000
        
        color = random.choice(COLORS)
        status = random.choices(STATUSES, weights=[0.6, 0.2, 0.2], k=1)[0]
        
        # New options and days in stock columns
        opc_options = ["Básico", "Intermediário", "Completo", "Premium", "Couro", "Teto Solar"]
        opc = random.choice(opc_options)
        dias_estoque = random.randint(0, 90)
        
        vehicles.append({
            "modelo": model,
            "opc": opc,
            "ano": year,
            "cor": color,
            "Dias estoque": dias_estoque,
            "Situação": status,
            "Placa": plate,
            "Chassi": chassi,
            "Marca": brand,
            "Preço": price
        })
        
    # Write to CSV
    filename = "estoque.csv"
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        fieldnames = ["modelo", "opc", "ano", "cor", "Dias estoque", "Situação", "Placa", "Chassi", "Marca", "Preço"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(vehicles)
        
    print(f"Gerado {filename} com sucesso contendo {len(vehicles)} veículos.")

if __name__ == "__main__":
    main()
