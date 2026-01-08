import streamlit as st
import pandas as pd
import database as db
import utils
import views.components as components
import datetime

def show_admin_view(user):
    st.title(f"Painel Administrativo - Bem-vindo, {user[4]}")
    
    tab1, tab2, tab3 = st.tabs(["Dashboard", "Gerenciar Produtos", "Gerenciar Usuários"])
    
    with tab1:
        # Aniversariantes do Dia
        birthday_clients = db.get_birthday_clients()
        if not birthday_clients.empty:
            today = datetime.date.today()
            birthdays_today = []
            
            for index, row in birthday_clients.iterrows():
                try:
                    bdate_str = str(row['birth_date'])
                    # Assume formato YYYY-MM-DD
                    bdate = datetime.datetime.strptime(bdate_str, "%Y-%m-%d").date()
                    if bdate.month == today.month and bdate.day == today.day:
                        birthdays_today.append(row)
                except:
                    pass
            
            if birthdays_today:
                st.error(f"🎉 ATENÇÃO: HOJE É ANIVERSÁRIO DE {len(birthdays_today)} CLIENTE(S)!")
                st.markdown("""
                <div style="background-color: #ffeebb; padding: 15px; border-radius: 10px; border: 2px solid #ffa500; margin-bottom: 20px;">
                    <h3 style="color: #d35400; margin-top: 0;">🎂 Oportunidade de Venda!</h3>
                    <p style="font-size: 16px;">
                        Lembre-se de enviar uma mensagem parabenizando e <b>sugerindo a compra de um presente especial</b> da loja!
                        Ofereça um desconto ou mostre os lançamentos.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                for b_client in birthdays_today:
                    st.markdown(f"🎈 **{b_client['name']}**")
                    st.text(f"📞 Telefone: {b_client['phone'] or 'Não informado'}")
                    st.text(f"📧 Email: {b_client['email'] or 'Não informado'}")
                    st.divider()

        st.header("Visão Geral")
        products = db.get_products()
        sales = db.get_sales_report()
        
        col1, col2, col3 = st.columns(3)
        
        total_stock = products['quantity'].sum() if not products.empty else 0
        total_sold = sales['quantity'].sum() if not sales.empty else 0
        total_revenue = sales['total_value'].sum() if not sales.empty else 0.0
        
        col1.metric("Produtos em Estoque", int(total_stock))
        col2.metric("Produtos Vendidos", int(total_sold))
        col3.metric("Receita Total", f"R$ {total_revenue:.2f}")

        # Nova linha de métricas
        st.subheader("Valores Totais")
        col4, col5 = st.columns(2)
        
        # Valor total em estoque (preço * quantidade para cada produto)
        total_stock_value = (products['price'] * products['quantity']).sum() if not products.empty else 0.0
        
        col4.metric("Valor Total em Estoque", f"R$ {total_stock_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        # Valor total vendido formatado com destaque
        formatted_revenue = f"R$ {total_revenue:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        col5.metric("Valor Total Vendido (Receita)", formatted_revenue)
        
        st.markdown(f"""
        <div style="background-color: #d4edda; padding: 10px; border-radius: 5px; color: #155724; font-weight: bold; margin-top: 10px; border: 1px solid #c3e6cb;">
            💰 VALOR TOTAL DOS PRODUTOS VENDIDOS: {formatted_revenue}
        </div>
        """, unsafe_allow_html=True)

        st.subheader("Estoque vs Vendas")
        if not products.empty or not sales.empty:
            chart_data = pd.DataFrame({
                'Categoria': ['Estoque', 'Vendidos'],
                'Quantidade': [total_stock, total_sold]
            })
            st.bar_chart(chart_data, x='Categoria', y='Quantidade', color="#800020")
            
        st.subheader("Últimas Vendas")
        if not sales.empty:
            st.dataframe(sales.sort_values(by='sale_date', ascending=False).head(10))
        else:
            st.info("Nenhuma venda registrada.")

        st.divider()
        st.subheader("Visualização Rápida de Produtos (Dashboard)")
        
        # Dashboard Product Grid (Simplified view, maybe allow sale)
        if not products.empty:
            # Area de Pesquisa no Dashboard
            search_term = st.text_input("🔍 Pesquisar Produto", placeholder="Nome, Marca, Estilo ou Tipo...", key="dash_search")
            
            if search_term:
                products = products[
                    products['name'].str.contains(search_term, case=False, na=False) |
                    products['brand'].str.contains(search_term, case=False, na=False) |
                    products['style'].str.contains(search_term, case=False, na=False) |
                    products['type'].str.contains(search_term, case=False, na=False) |
                    products['id'].astype(str).str.contains(search_term, case=False, na=False) |
                    products['price'].astype(str).str.contains(search_term, case=False, na=False) |
                    products['quantity'].astype(str).str.contains(search_term, case=False, na=False) |
                    products['expiration_date'].astype(str).str.contains(search_term, case=False, na=False)
                ]

            cols_per_row = 4
            rows = len(products)
            
            for i in range(0, rows, cols_per_row):
                cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    if i + j < rows:
                        row = products.iloc[i + j]
                        with cols[j]:
                            with st.container(border=True):
                                # Image
                                img_src = utils.get_product_image_source(row)
                                if img_src:
                                    st.image(img_src, use_container_width=True)
                                else:
                                    st.markdown("*Sem Imagem*")
                                    
                                st.markdown(f"**{row['name']}**")
                                st.caption(f"Estoque: {row['quantity']}")
                                st.markdown(f"**R$ {row['price']:.2f}**")
                                st.caption(f"Val: {row['expiration_date']}")
                                
                                # Quick Sale Action
                                if row['quantity'] > 0:
                                    with st.expander("Vender"):
                                        q_sell = st.number_input("Qtd", 1, int(row['quantity']), key=f"dash_sell_{row['id']}")
                                        if st.button("OK", key=f"dash_btn_{row['id']}"):
                                            success, msg = db.register_sale(int(row['id']), q_sell, user[0])
                                            if success:
                                                st.toast(msg, icon="✅")
                                                st.rerun()
                                            else:
                                                st.toast(msg, icon="❌")
        else:
            st.info("Nenhum produto cadastrado.")

    with tab2:
        components.render_product_management()

    with tab3:
        st.header("Gerenciar Usuários")
        with st.form("add_user"):
            new_user = st.text_input("Username")
            new_pass = st.text_input("Senha", type="password")
            new_role = st.selectbox("Função", ["admin", "funcionario", "cliente"])
            new_name = st.text_input("Nome Completo")
            
            st.markdown("---")
            st.caption("Informações Adicionais (Para Clientes)")
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                new_birth_date = st.date_input("Data de Nascimento", value=None, min_value=datetime.date(1920, 1, 1), format="DD/MM/YYYY")
                new_email = st.text_input("Email")
            with col_u2:
                new_phone = st.text_input("Telefone")
                new_cpf = st.text_input("CPF")
            
            st.caption("Preferências do Cliente")
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                pref_type = st.multiselect("Tipos Favoritos", utils.TIPOS)
            with col_p2:
                pref_brand = st.multiselect("Marcas Favoritas", utils.MARCAS)
            with col_p3:
                pref_style = st.multiselect("Estilos Favoritos", utils.ESTILOS)

            if st.form_submit_button("Criar Usuário"):
                if new_user and new_pass:
                    # Converter data para string
                    bdate_val = str(new_birth_date) if new_birth_date else None
                    
                    # Converter preferências
                    p_type_str = ", ".join(pref_type) if pref_type else None
                    p_brand_str = ", ".join(pref_brand) if pref_brand else None
                    p_style_str = ", ".join(pref_style) if pref_style else None
                    
                    if db.create_user(new_user, new_pass, new_role, new_name, bdate_val, new_email, new_phone, new_cpf,
                                      preferred_type=p_type_str, preferred_brand=p_brand_str, preferred_style=p_style_str):
                        st.success("Usuário criado!")
                        st.rerun()
                    else:
                        st.error("Erro ao criar (usuário já existe?)")
                else:
                    st.error("Preencha todos os campos obrigatórios")
                    
        st.subheader("Usuários Existentes")
        conn = db.get_connection()
        # Update query to show new fields if needed, but dataframe might get too wide. 
        # Keeping it simple or maybe showing email/phone.
        users_df = pd.read_sql("SELECT id, username, role, name, email, phone FROM users", conn)
        conn.close()
        st.dataframe(users_df)
