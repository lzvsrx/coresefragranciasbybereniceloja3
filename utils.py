import streamlit as st
import base64
import io
from pathlib import Path

# Constantes do Sistema
MARCAS = [
    "Eudora", "O Boticário", "Jequiti", "Avon", "Mary Kay", "Natura", 
    "Oui-Original-Unique-Individuel", "Pierre Alexander", "Tupperware", "Outra"
]

ESTILOS = [
    "Perfumaria", "Skincare", "Cabelo", "Corpo e Banho", "Make", "Masculinos", 
    "Femininos Nina Secrets", "Marcas", "Infantil", "Casa", "Solar", "Maquiage", 
    "Teen", "Kits e Presentes", "Cuidados com o Corpo", "Lançamentos", 
    "Acessórios de Casa", "Outro"
]

TIPOS = [
    "Perfumaria masculina", "Perfumaria feminina", "Body splash", "Body spray", 
    "Eau de parfum", "Desodorantes", "Perfumaria infantil", "Perfumaria vegana", 
    "Família olfativa", "Clareador de manchas", "Anti-idade", "Protetor solar facial", 
    "Rosto", "Tratamento para o rosto", "Acne", "Limpeza", "Esfoliante", "Tônico facial", 
    "Kits de tratamento", "Tratamento para cabelos", "Shampoo", "Condicionador", 
    "Leave-in e Creme para Pentear", "Finalizador", "Modelador", "Acessórios", 
    "Kits e looks", "Boca", "Olhos", "Pincis", "Paleta", "Unhas", "Sobrancelhas", 
    "Hidratante", "Cuidados pós-banho", "Cuidados para o banho", "Barba", "Óleo corporal", 
    "Cuidados íntimos", "Unissex", "Bronzeamento", "Protetor solar", "Depilação", 
    "Mãos", "Lábios", "Pés", "Pés sol", "Protetor solar corporal", "Colônias", 
    "Estojo", "Sabonetes", "Sabonete líquido", "Sabonete em barra", 
    "Creme hidratante para as mãos", "Creme hidratante para os pés", "Miniseries", 
    "Kits de perfumes", "Antissinais", "Máscara", "Creme bisnaga", 
    "Roll On Fragrânciado", "Roll On On Duty", "Shampoo 2 em 1", "Spray corporal", 
    "Booster de Tratamento", "Creme para Pentear", "Óleo de Tratamento", 
    "Pré-shampoo", "Sérum de Tratamento", "Shampoo e Condicionador", "Garrafas", 
    "Armazenamentos", "Micro-ondas", "Servir", "Preparo", "Lazer/Outdoor", 
    "Presentes", "Outro"
]

# Paleta de Cores
COLOR_BG = "#FFFFE0"
COLOR_TEXT_SMALL = "#36454F"
COLOR_TEXT_LARGE_1 = "#800020"
COLOR_TEXT_LARGE_2 = "#36454F"

import os

def get_product_image_source(product_row):
    """
    Returns the image source for st.image.
    Fetches directly from database blob to ensure persistence.
    Ignores local file system to avoid issues with ephemeral storage (Streamlit Cloud).
    """
    img_data = product_row.get('image')
    
    # Se houver dados e forem bytes não vazios
    if img_data is not None and isinstance(img_data, bytes) and len(img_data) > 0:
        return io.BytesIO(img_data)
        
    return None



def ensure_directories():
    """Garante que diretórios essenciais existam"""
    try:
        Path("assets").mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Erro ao criar diretórios: {e}")

def apply_custom_css():
    st.markdown("""
        <style>
        html, body, .stApp {
            background-color: #FFFFE0 !important;
        }
        .stApp, .stApp p, .stApp span, .stApp div {
            color: #36454F;
        }

        h1, h2, h3, h4, h5, h6, strong, b, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
            color: #800020;
        }

        .st-emotion-cache-hzygls,
        .st-emotion-cache-4man113,
        div[data-testid="stStatusContainer"],
        div[data-testid="stCacheContainer"] {
            background-color: #FFFACD !important;
            color: #36454F !important;
            padding: 5px;
            border-radius: 3px;
        }

        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: #FFFACD; /* Amarelo-claro Pálido (OPACO) */
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb {
            background: #800020; /* Vermelho-vinho (OPACO) */
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: #FFFACD; /* Amarelo-claro Pálido (OPACO) */
        }

        * {
            scrollbar-color: #800020 #FFFACD;
            scrollbar-width: thin;
        }

        *::-moz-scrollbar-thumb:hover {
            background: #FFFACD; /* Amarelo-claro Pálido no hover do Thumb (OPACO) */
        }

        header,
        header.st-emotion-cache-18nibws,
        header.st-emotion-cache-1rq341t,
        header.st-emotion-cache-1l02z8d,
        div[data-testid="stHeader"] {
            background-color: #FFFFE0 !important;
        }

        /* RODAPÉ (Footer) */
        footer,
        div[data-testid="stFooter"] {
            background-color: #FFFFE0 !important;
            color: #36454F !important;
        }
        footer a,
        div[data-testid="stFooter"] a {
            color: #800020 !important;
        }

        /* SIDEBAR (Barra de Navegação) */
        .stSidebar,
        .stSidebar > div:first-child,
        div[data-testid="stSidebar"] {
            background-color: #FFFFE0 !important;
        }
        .stSidebar .stMarkdown, .stSidebar .stSelectbox label,
        .stSidebar p, .stSidebar span {
            color: #36454F !important;
        }

        /* LINKS DE NAVEGAÇÃO NA BARRA LATERAL */
        .stSidebar nav ul li a, .stSidebar nav ul li div[role="button"],
        div[data-testid="stVerticalNav"] li a {
            background-color: #FFFFE0 !important;
            color: #36454F !important;
        }
        .stSidebar nav ul li a:hover, .stSidebar nav ul li div[role="button"]:hover,
        div[data-testid="stVerticalNav"] li a:hover {
            background-color: #FFFACD !important;
            color: #800020 !important;
        }
        .stSidebar nav ul li a[aria-current="page"], .stSidebar nav ul li div[aria-selected="true"],
        div[data-testid="stVerticalNav"] li a[aria-current="page"] {
            background-color: #FFFACD !important;
            color: #800020 !important;
            font-weight: bold;
        }

        /* Menu Principal (Menu Hambúrguer) */
        div[data-testid="stMainMenu"] {
            background-color: #FFFFE0 !important;
        }
        div[data-testid="stMainMenu"] button, div[data-testid="stMainMenu"] div {
            color: #36454F !important;
            background-color: #FFFFE0 !important;
        }
        div[data-testid="stMainMenu"] button:hover, div[data-testid="stMainMenu"] div:hover {
            background-color: #FFFACD !important;
            color: #800020 !important;
        }


        /* ------------------------------------------------------------------ */
        /* FORMULÁRIOS E INPUTS */
        /* ------------------------------------------------------------------ */

        /* FORMULÁRIOS (st.form) */
        .stForm {
            background-color: #FFFFE0;
            border: 1px solid #FFFACD;
            padding: 10px;
            border-radius: 5px;
        }

        /* INPUTS DE TEXTO GERAIS (Cobre: st.text_input, st.number_input, st.date_input, st.text_area, st.selectbox) */
        .stTextInput>div>div>input,
        .stNumberInput>div>div>input,
        .stDateInput>div>div>input,
        .stTextArea>div>div>textarea,
        .stSelectbox div[data-baseweb="select"] div[role="button"],
        .stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea,
        div[data-testid="stSelectbox"] div[role="button"] {
            background-color: #FFFACD !important; /* Amarelo-claro Pálido */
            color: #36454F !important;
            border-color: #800020 !important;
            
            -webkit-appearance: none;
            -moz-appearance: none;
            appearance: none;
            -webkit-transition: border-color 0.3s ease, box-shadow 0.3s ease;
            transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }

        /* Foco nos Inputs - Suporte Cross-Browser para Focus Ring! */
        .stTextInput>div>div>input:focus,
        .stNumberInput>div>div>input:focus,
        .stDateInput>div>div>input:focus,
        .stTextArea>div>div>textarea:focus,
        .stTextInput input:focus, .stNumberInput input:focus, .stDateInput input:focus, .stTextArea textarea:focus {
            border-color: #800020 !important;
            
            -webkit-box-shadow: 0 0 0 1px #800020 !important;
            -moz-box-shadow: 0 0 0 1px #800020 !important;
            box-shadow: 0 0 0 1px #800020 !important;
            
            outline: none !important;
        }

        /* CHAT INPUT (st.chat_input) */
        .stChatInputContainer,
        div[data-testid="stChatInput"] {
            background-color: #FFFFE0 !important;
            border-top: 1px solid #FFFACD;
            padding: 10px 0;
        }
        .stChatInputContainer input,
        div[data-testid="stChatInput"] input {
            background-color: #FFFACD !important;
            color: #36454F !important;
            border-color: #800020 !important;
        }
        .stChatInputContainer button svg,
        div[data-testid="stChatInput"] button svg {
            fill: #800020 !important;
        }
        .stChatInputContainer button,
        div[data-testid="stChatInput"] button {
            background-color: #FFFACD !important;
            border-color: #800020 !important;
        }
        .stChatInputContainer button:hover,
        div[data-testid="stChatInput"] button:hover {
            background-color: #FFFFE0 !important;
        }
        .stButton>button,
        div[data-testid="baseButton-secondary"] button {
            background-color: #FFFACD;
            color: #800020;
            border-color: #800020;
            
            -webkit-transition: all 0.2s ease-in-out;
            transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover,
        div[data-testid="baseButton-secondary"] button:hover {
            background-color: #800020 !important;
            color: #FFFACD !important;
            border-color: #800020 !important;
        }
        </style>
    """, unsafe_allow_html=True)

from fpdf import FPDF
import pandas as pd

def generate_pdf(products_df):
    pdf = FPDF()
    pdf.add_page()
    # Usar fonte padrão que suporta caracteres básicos, mas para caracteres especiais complexos
    # FPDF padrão tem limitações. Vamos tentar limpar o texto ou usar codificação 'latin-1' compatível
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="Relatório de Produtos", ln=1, align='C')
    pdf.ln(10)
    
    for index, row in products_df.iterrows():
        # Função auxiliar para limpar/substituir caracteres problemáticos
        def clean_text(text):
            try:
                # Tenta codificar e decodificar para garantir compatibilidade com latin-1
                return str(text).encode('latin-1', 'replace').decode('latin-1')
            except Exception:
                return "?"

        # Truncate text to avoid overflow if necessary, or just simple list
        try:
            text = f"ID: {row['id']} | Nome: {clean_text(str(row['name'])[:30])} | Marca: {clean_text(str(row['brand'])[:15])}"
            text2 = f"   Qtd: {row['quantity']} | Preço: R$ {row['price']} | Val: {row['expiration_date']}"
            pdf.cell(0, 8, txt=text, ln=1)
            pdf.cell(0, 8, txt=text2, ln=1)
            pdf.ln(2)
        except Exception as e:
            print(f"Erro ao gerar linha PDF: {e}")
            pdf.cell(0, 8, txt="Erro ao processar linha", ln=1)
        
    try:
        output = pdf.output(dest='S')
        return output.encode('latin-1', 'replace') if isinstance(output, str) else bytes(output)
    except Exception as e:
        return b""

def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')
