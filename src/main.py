# -*- coding: utf-8 -*-
import os
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template_string, Response, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import re # Para extrair título
from weasyprint import HTML, CSS # Para gerar PDF
from datetime import datetime
import traceback # Para logs de erro mais detalhados

# Configuração inicial do Flask
app = Flask(__name__, template_folder="../templates") # Aponta para a pasta templates um nível acima
app.config["SECRET_KEY"] = os.urandom(24) # Chave secreta para sessões

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login" # Rota para redirecionar se não estiver logado

# Configuração da API Key do Google Gemini (NECESSÁRIO CONFIGURAR)
# Obtenha sua chave em https://aistudio.google.com/app/apikey
# É recomendado usar variáveis de ambiente para segurança
API_KEY = os.getenv("GEMINI_API_KEY", "SUA_API_KEY_AQUI")
if API_KEY == "SUA_API_KEY_AQUI":
    print("AVISO: Chave da API Gemini não configurada. A geração de receitas não funcionará.")
else:
    try:
        genai.configure(api_key=API_KEY)
        print("API Key do Gemini configurada com sucesso.")
    except Exception as e:
        # CORRIGIDO: f-string única
        print(f"Erro ao configurar a API Key do Gemini: {e}")
        API_KEY = "SUA_API_KEY_AQUI" # Reseta para evitar chamadas inválidas

# Modelo de usuário para Flask-Login (exemplo simples em memória)
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Simulação de banco de dados de usuários (substituir por um real)
users = {"1": User("1")} # Exemplo: usuário com id "1"

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# Simulação de "banco de dados" em memória para receitas
recipes_db = {
    "Café da Manhã": {
        "Geral": [],
        "Saudável": [],
        "Rápido": [],
    },
    "Almoço": {
        "Geral": [],
        "Vegano": [],
        "Low Carb": [],
        "Rápido": [],
        "Econômico": [],
    },
    "Jantar": {
        "Geral": [],
        "Leve": [],
        "Sofisticado": [],
    },
    "Sobremesa": {
        "Geral": [],
        "Chocolate": [],
        "Frutas": [],
        "Fit": [],
    },
    "Lanches": {
        "Geral": [],
        "Salgado": [],
        "Doce": [],
        "Pré-treino": [],
    }
}

# Função auxiliar para adicionar receita ao "DB"
def add_recipe_to_db(category, subcategory, recipe_data):
    effective_subcategory = subcategory if subcategory in recipes_db.get(category, {}) else "Geral"
    if category in recipes_db and effective_subcategory in recipes_db[category]:
        recipes_db[category][effective_subcategory].append(recipe_data)
        if subcategory != effective_subcategory:
             # CORRIGIDO: Usar f-string única e correta
             print(f"Aviso: Subcategoria '{subcategory}' não encontrada em '{category}'. Adicionando em '{effective_subcategory}'.")
        return True
    elif category in recipes_db and "Geral" in recipes_db[category]:
         recipes_db[category]["Geral"].append(recipe_data)
         # CORRIGIDO: Usar f-string única e correta
         print(f"Aviso: Subcategoria '{subcategory}' inválida para '{category}'. Adicionando em 'Geral'.")
         return True
    else:
        # CORRIGIDO: Usar f-string única e correta
        print(f"Erro: Categoria '{category}' não encontrada no banco de dados.")
        return False

# Função para tentar extrair o título da receita do texto gerado
def extract_title(recipe_text):
    lines = recipe_text.strip().split("\n")
    if not lines:
        return "Receita Gerada (Texto Vazio)"
    potential_title = lines[0].strip()
    potential_title = re.sub(r"^[\*#]+\s*|\s*[\*#]+$", "", potential_title)
    if len(potential_title) < 80 and len(potential_title) > 3:
        return potential_title
    if len(lines) > 1 and (len(potential_title) <= 3 or potential_title.lower() == "receita"):
        potential_title_2 = lines[1].strip()
        potential_title_2 = re.sub(r"^[\*#]+\s*|\s*[\*#]+$", "", potential_title_2)
        if len(potential_title_2) < 80 and len(potential_title_2) > 3:
            return potential_title_2
    return "Receita Gerada (Título não extraído)"

# --- Rotas de Autenticação (Exemplo Básico) ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        # Simplesmente aceita qualquer login para este exemplo
        user = users.get("1")
        if user:
            login_user(user)
            return jsonify({"message": "Login bem-sucedido! Redirecionando...", "redirect": "/"})
        # Na prática, você validaria o usuário/senha aqui
        return "Usuário ou senha inválidos", 401
    # Formulário de login com design mais leve (Ajustado)
    return render_template_string("""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Login - App de Receitas</title>
            <style>
                /* Adiciona link para fonte Inter */
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

                body {
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    background-color: #f7f7f7; /* Fundo ainda mais claro */
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                }
                .login-container {
                    background-color: #ffffff;
                    padding: 40px 50px;
                    border-radius: 12px; /* Bordas mais arredondadas */
                    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06); /* Sombra um pouco mais pronunciada */
                    text-align: center;
                    max-width: 360px; /* Um pouco mais estreito */
                    width: 90%;
                }
                h2 {
                    color: #333; /* Cor de título um pouco mais suave */
                    margin-bottom: 30px; /* Mais espaço abaixo do título */
                    font-weight: 600;
                    font-size: 1.6em;
                }
                .input-group {
                    margin-bottom: 20px; /* Mais espaço entre os campos */
                    text-align: left;
                }
                label {
                    display: block;
                    margin-bottom: 8px; /* Mais espaço abaixo do label */
                    color: #555; /* Cor de label mais escura */
                    font-size: 0.9em;
                    font-weight: 500;
                }
                input[type="text"],
                input[type="password"] {
                    width: 100%;
                    padding: 12px 15px; /* Campos um pouco maiores */
                    border: 1px solid #ddd; /* Borda mais sutil */
                    border-radius: 8px; /* Bordas mais arredondadas para inputs */
                    box-sizing: border-box;
                    font-size: 1em;
                    transition: border-color 0.2s ease, box-shadow 0.2s ease;
                }
                input[type="text"]:focus,
                input[type="password"]:focus {
                    outline: none;
                    border-color: #a0cfff; /* Azul bem claro no foco */
                    box-shadow: 0 0 0 3px rgba(0, 110, 255, 0.1);
                }
                input[type="submit"] {
                    background: linear-gradient(to right, #6a11cb 0%, #2575fc 100%); /* Gradiente estilo Gamma */
                    color: white;
                    border: none;
                    padding: 14px 20px; /* Botão maior */
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 1.05em;
                    font-weight: 500;
                    width: 100%;
                    transition: opacity 0.2s ease, transform 0.1s ease;
                    margin-top: 20px; /* Mais espaço acima do botão */
                    box-shadow: 0 4px 10px rgba(0, 123, 255, 0.2);
                }
                input[type="submit"]:hover {
                    opacity: 0.9;
                }
                 input[type="submit"]:active {
                    transform: scale(0.97);
                    box-shadow: 0 2px 5px rgba(0, 123, 255, 0.2);
                 }
                p {
                    color: #888; /* Cinza mais claro */
                    font-size: 0.85em;
                    margin-top: 25px;
                }
            </style>
        </head>
        <body>
            <div class="login-container">
                <h2>Login</h2>
                <form method="post">
                    <div class="input-group">
                        <label for="username">Usuário:</label>
                        <input type="text" id="username" name="username" value="user" required>
                    </div>
                    <div class="input-group">
                        <label for="password">Senha:</label>
                        <input type="password" id="password" name="password" value="pass" required>
                    </div>
                    <input type="submit" value="Entrar">
                </form>
                <p>(Use usuário "user" e senha "pass")</p>
            </div>
        </body>
        </html>
    """)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout bem-sucedido!"})

# --- Rotas Principais do App ---
@app.route("/")
@login_required
def home():
    # Lê o conteúdo do index.html a cada requisição (bom para desenvolvimento)
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            template_content = f.read()
        return render_template_string(template_content)
    except FileNotFoundError:
        # CORRIGIDO: f-string única
        print("Erro Crítico: Arquivo de template 'templates/index.html' não encontrado.")
        return "Erro interno: Arquivo de template principal não encontrado.", 500
    except Exception as e:
        # CORRIGIDO: f-string única
        print(f"Erro ao ler template 'templates/index.html': {e}\n{traceback.format_exc()}")
        return "Erro interno ao carregar a página.", 500

# --- Rota para Geração de Receitas ---
@app.route("/generate_recipe", methods=["POST"])
@login_required
def generate_recipe_route():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Requisição sem dados JSON."}), 400
    category = data.get("category")
    subcategory = data.get("subcategory", "")
    ingredients = data.get("ingredients", [])
    if not category:
         return jsonify({"error": "Categoria é obrigatória."}), 400
    if category not in recipes_db:
         # CORRIGIDO: Usar f-string única
         return jsonify({"error": f"Categoria '{category}' inválida."}), 400

    # CORRIGIDO: Usar f-string única para montar o prompt
    prompt = f"Gere uma receita detalhada para a categoria '{category}'"
    if subcategory:
        prompt += f" com foco específico em '{subcategory}'"
    if ingredients:
        ingredients_str = ", ".join(ingredients[:10]) # Limita a 10 ingredientes no prompt
        prompt += f" usando principalmente os seguintes ingredientes: {ingredients_str}"
    prompt += ". A receita deve incluir um título claro e chamativo, a lista de ingredientes completa com quantidades exatas, instruções passo a passo bem detalhadas e o tempo estimado de preparo total."
    prompt += " Formate a resposta de forma clara e organizada, usando markdown para títulos, listas e negrito quando apropriado."

    try:
        if API_KEY == "SUA_API_KEY_AQUI":
            # CORRIGIDO: f-string única
            print("Tentativa de gerar receita sem API Key configurada.")
            return jsonify({"error": "API Key do Gemini não configurada no servidor."}), 500

        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        # CORRIGIDO: f-string única
        print(f"Gerando receita com prompt: {prompt[:200]}...") # Log do início do prompt
        response = model.generate_content(prompt)

        # Verifica se a resposta foi bloqueada
        if not response.parts:
             block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else "Não especificado"
             # CORRIGIDO: f-string única
             print(f"Resposta bloqueada pela API Gemini. Razão: {block_reason}")
             # CORRIGIDO: f-string única
             return jsonify({"error": f"A geração da receita foi bloqueada por políticas de segurança. Razão: {block_reason}"}), 400

        recipe_text = response.text
        recipe_title = extract_title(recipe_text)
        # Cria um ID mais robusto e único
        recipe_id = f"{category.replace(' ', '_')}_{subcategory.replace(' ', '_') if subcategory else 'Geral'}_{int(datetime.now().timestamp() * 1000)}"

        recipe_data = {
            "id": recipe_id,
            "title": recipe_title,
            "category": category,
            "subcategory": subcategory if subcategory else "Geral",
            "full_text": recipe_text,
            "is_favorite": False # Inicialmente não é favorito
        }

        if add_recipe_to_db(category, subcategory, recipe_data):
             # CORRIGIDO: Usar f-string única
             print(f"Receita '{recipe_title}' adicionada a {category}/{recipe_data['subcategory']}")
        else:
             # A função add_recipe_to_db já imprime o erro
             return jsonify({"error": "Falha ao salvar a receita gerada internamente."}), 500

        return jsonify(recipe_data)

    except Exception as e:
        # CORRIGIDO: Usar f-string única
        print(f"Erro ao chamar a API Gemini ou processar a resposta: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Falha ao gerar ou processar a receita. Verifique os logs do servidor."}), 500

# --- Rotas para Listar Categorias e Receitas ---
@app.route("/categories", methods=["GET"])
@login_required
def get_categories():
    structured_categories = {}
    for cat, sub_dict in recipes_db.items():
        # Inclui subcategorias que têm receitas ou são 'Geral'
        valid_subcategories = [sub for sub, recipes in sub_dict.items() if recipes or sub == "Geral"]
        if valid_subcategories:
             structured_categories[cat] = sorted(valid_subcategories)
    return jsonify(structured_categories)

@app.route("/recipes", methods=["GET"])
@login_required
def get_all_recipes():
    all_recipes = []
    # Obtém a lista de favoritos do localStorage (passada como query param pelo frontend)
    favorite_ids = request.args.getlist("favorites[]") # Espera 'favorites[]' do JS
    for category, subcategories in recipes_db.items():
        for subcategory, recipes in subcategories.items():
            for recipe in recipes:
                 # Cria uma cópia para não modificar o DB original
                 recipe_copy = recipe.copy()
                 recipe_copy["is_favorite"] = recipe["id"] in favorite_ids
                 all_recipes.append(recipe_copy)
    return jsonify(all_recipes)

@app.route("/recipes/<category>", methods=["GET"])
@login_required
def get_recipes_by_category(category):
    if category not in recipes_db:
        return jsonify({"error": "Categoria não encontrada"}), 404
    all_recipes_in_category = []
    favorite_ids = request.args.getlist("favorites[]")
    for sub, recipes in recipes_db[category].items():
         for recipe in recipes:
             recipe_copy = recipe.copy()
             recipe_copy["is_favorite"] = recipe["id"] in favorite_ids
             all_recipes_in_category.append(recipe_copy)
    return jsonify(all_recipes_in_category)

@app.route("/recipes/<category>/<subcategory>", methods=["GET"])
@login_required
def get_recipes_by_subcategory(category, subcategory):
    if category not in recipes_db:
        return jsonify({"error": "Categoria não encontrada"}), 404
    target_subcategory = subcategory if subcategory else "Geral"
    favorite_ids = request.args.getlist("favorites[]")
    recipes_to_return = []
    if target_subcategory not in recipes_db[category]:
        if "Geral" in recipes_db[category]:
             # CORRIGIDO: Usar f-string única
             print(f"Subcategoria '{target_subcategory}' não encontrada, retornando 'Geral' para '{category}'.")
             recipes_to_return = recipes_db[category]["Geral"]
        else:
             return jsonify({"error": "Subcategoria não encontrada"}), 404
    else:
        recipes_to_return = recipes_db[category][target_subcategory]

    recipes_processed = []
    for recipe in recipes_to_return:
        recipe_copy = recipe.copy()
        recipe_copy["is_favorite"] = recipe["id"] in favorite_ids
        recipes_processed.append(recipe_copy)
    return jsonify(recipes_processed)

# --- Rota para Gerar PDF --- #
@app.route("/generate_pdf", methods=["GET"])
@login_required
def generate_pdf_route():
    category = request.args.get("category")
    subcategory = request.args.get("subcategory")
    recipe_ids = request.args.getlist("ids[]") # Espera 'ids[]' do JS
    favorites_only = request.args.get("favorites_only") == "true"
    favorite_ids_for_pdf = request.args.getlist("favorites[]") # IDs favoritos atuais

    recipes_to_include = []
    pdf_title = "Meu Livro de Receitas"

    # Coleta todas as receitas primeiro para facilitar a filtragem por ID ou favoritos
    all_recipes_flat = []
    for cat_dict in recipes_db.values():
        for sub_list in cat_dict.values():
            all_recipes_flat.extend(sub_list)

    if favorites_only:
        if not favorite_ids_for_pdf:
             return jsonify({"error": "Nenhum ID de receita favorito fornecido para gerar o PDF."}), 400
        pdf_title = "Minhas Receitas Favoritas"
        recipes_to_include = [r for r in all_recipes_flat if r["id"] in favorite_ids_for_pdf]

    elif recipe_ids:
        pdf_title = "Seleção de Receitas"
        recipes_to_include = [r for r in all_recipes_flat if r["id"] in recipe_ids]

    elif category and category != "all":
        pdf_title = f"Receitas de {category}"
        if subcategory and subcategory != "all":
            pdf_title += f" - {subcategory}"
            if category in recipes_db and subcategory in recipes_db[category]:
                recipes_to_include = recipes_db[category][subcategory]
            elif category in recipes_db and "Geral" in recipes_db[category]:
                 recipes_to_include = recipes_db[category]["Geral"]
        else: # Todas as subcategorias da categoria
            if category in recipes_db:
                for sub_list in recipes_db[category].values():
                    recipes_to_include.extend(sub_list)
    else: # Todas as receitas
        pdf_title = "Todas as Receitas"
        recipes_to_include = all_recipes_flat

    if not recipes_to_include:
        return jsonify({"error": "Nenhuma receita encontrada para gerar o PDF com os filtros fornecidos."}), 404

    # Gera o HTML para o PDF
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset=\"UTF-8\">
        <title>{pdf_title}</title>
        <style>
            @page {{ margin: 2cm; }}
            body {{ font-family: 'Helvetica', 'Arial', sans-serif; line-height: 1.5; color: #333; }}
            h1 {{ text-align: center; color: #4CAF50; border-bottom: 2px solid #ddd; padding-bottom: 10px; margin-bottom: 1.5cm; }}
            .recipe {{ page-break-inside: avoid; margin-bottom: 2cm; border-top: 1px solid #eee; padding-top: 1cm; }}
            h2 {{ color: #333; margin-bottom: 0.5cm; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
            p.category-info {{ font-style: italic; color: #777; margin-bottom: 1cm; font-size: 0.9em; }}
            pre {{ 
                white-space: pre-wrap; /* Mantém quebras de linha e espaços */
                word-wrap: break-word; /* Quebra palavras longas */
                background-color: #f9f9f9; 
                padding: 15px; 
                border-radius: 5px; 
                border: 1px solid #eee; 
                font-family: 'Courier New', Courier, monospace; /* Fonte monoespaçada */
                font-size: 0.9em;
                line-height: 1.6;
            }}
        </style>
    </head>
    <body>
        <h1>{pdf_title}</h1>
    """
    for recipe in recipes_to_include:
        # Limpa um pouco o título para o nome do arquivo
        safe_title = re.sub(r'[^\w\- ]+', '', recipe["title"]).replace(' ', '_') # Mantém espaços e hífens, substitui outros por nada
        html_content += f"""
        <div class=\"recipe\">
            <h2>{recipe["title"]}</h2>
            <p class=\"category-info\"><i>Categoria: {recipe["category"]} / {recipe["subcategory"]}</i></p>
            <pre>{recipe["full_text"]}</pre>
        </div>
        """
    html_content += "</body></html>"

    try:
        # Gera o PDF usando WeasyPrint
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        # Cria a resposta Flask
        response = make_response(pdf_bytes)
        response.headers["Content-Type"] = "application/pdf"
        # Nome do arquivo para download
        safe_pdf_title = re.sub(r'[^\w\- ]+', '', pdf_title).replace(' ', '_')
        response.headers["Content-Disposition"] = f"attachment; filename=\"{safe_pdf_title}.pdf\""
        # CORRIGIDO: f-string única
        print(f"Gerando PDF: {safe_pdf_title}.pdf")
        return response

    except Exception as e:
        # CORRIGIDO: Usar f-string única
        print(f"Erro ao gerar PDF com WeasyPrint: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "Falha ao gerar o arquivo PDF."}), 500


if __name__ == "__main__":
    # Executa o app Flask
    # debug=False é importante para produção, mas pode ser True para desenvolvimento
    # CORRIGIDO: f-string única
    print("Iniciando servidor Flask...")
    app.run(host="0.0.0.0", port=5000, debug=False)

