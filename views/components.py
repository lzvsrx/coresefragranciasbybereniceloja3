import streamlit as st
import pandas as pd
import database as db
import utils
import datetime

def render_product_management():
    st.header("Gerenciamento de Produtos")
    
    # Add Product Form
    with st.expander("Adicionar Novo Produto"):
        with st.form("add_product_form_comp"):
            name = st.text_input("Nome do Produto")
            col_a, col_b = st.columns(2)
            brand = col_a.selectbox("Marca", utils.MARCAS)
            style = col_b.selectbox("Estilo", utils.ESTILOS)
            type_ = st.selectbox("Tipo", utils.TIPOS)
            
            col_c, col_d, col_e = st.columns(3)
            price = col_c.number_input("Preço (R$)", min_value=0.01, format="%.2f")
            quantity = col_d.number_input("Quantidade", min_value=1, step=1)
            exp_date = col_e.date_input("Data de Vencimento")
            
            image = st.file_uploader("Imagem do Produto", type=['png', 'jpg', 'jpeg'])
            
            submitted = st.form_submit_button("Cadastrar Produto")
            if submitted:
                # Validação de Erros
                errors = []
                
                if not name or not name.strip():
                    errors.append("O nome do produto é obrigatório.")
                
                if price <= 0:
                    errors.append("O preço deve ser maior que zero.")
                    
                if quantity < 0:
                    errors.append("A quantidade não pode ser negativa.")
                
                # Processamento da Imagem
                img_bytes = None
                if image:
                    try:
                        # Limite de tamanho (ex: 10MB)
                        if image.size > 10 * 1024 * 1024:
                            errors.append("A imagem é muito grande (máximo 10MB).")
                        else:
                            img_bytes = image.read()
                    except Exception as e:
                        errors.append(f"Erro ao processar a imagem: {e}")
                
                if errors:
                    for err in errors:
                        st.error(f"❌ {err}")
                else:
                    try:
                        db.add_product(name.strip(), brand, style, type_, price, quantity, str(exp_date), img_bytes)
                        st.success("✅ Produto cadastrado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar no banco de dados: {e}")

    # Import/Export Section
    with st.expander("Importar / Exportar Dados"):
        col_ie1, col_ie2 = st.columns(2)
        products_df_ex = db.get_products()
        
        with col_ie1:
            st.write("### Exportar")
            if not products_df_ex.empty:
                pdf_bytes = utils.generate_pdf(products_df_ex)
                st.download_button("Baixar PDF", data=pdf_bytes, file_name="produtos.pdf", mime="application/pdf", key="pdf_dl")
                
                csv_data = utils.convert_df_to_csv(products_df_ex.drop(columns=['image']).rename(columns={
                    'name': 'nome', 'brand': 'marca', 'style': 'estilo', 
                    'type': 'tipo', 'price': 'preco', 'quantity': 'quantidade', 
                    'expiration_date': 'data_validade'
                }))
                st.download_button("Exportar CSV", data=csv_data, file_name="produtos.csv", mime="text/csv", key="csv_dl")
            else:
                st.info("Sem dados para exportar.")

        with col_ie2:
            st.write("### Importar")
            uploaded_csv = st.file_uploader("Arquivo CSV", type=['csv'], key="csv_up")
            if uploaded_csv:
                if st.button("Processar Importação", key="btn_import"):
                    try:
                        # Tenta detectar o separador automaticamente
                        imported_df = pd.read_csv(uploaded_csv, sep=None, engine='python')
                        
                        # Validar se as colunas mínimas existem
                        # Colunas esperadas: nome, marca, estilo, tipo, preco, quantidade, data_validade
                        # Vamos ser flexíveis, mas 'nome' é essencial
                        if 'nome' not in imported_df.columns:
                            st.error("❌ O arquivo CSV deve conter pelo menos a coluna 'nome'.")
                        else:
                            success_count = 0
                            fail_count = 0
                            error_log = []
                            
                            progress_bar = st.progress(0)
                            total_rows = len(imported_df)
                            
                            for index, row in imported_df.iterrows():
                                try:
                                    p_name = str(row.get('nome', '')).strip()
                                    if not p_name:
                                        raise ValueError("Nome do produto vazio")
                                    
                                    p_brand = str(row.get('marca', 'Outra'))
                                    # Opcional: validar se a marca está na lista permitida, senão usar 'Outra'
                                    if p_brand not in utils.MARCAS: p_brand = 'Outra'
                                        
                                    p_style = str(row.get('estilo', 'Outro'))
                                    if p_style not in utils.ESTILOS: p_style = 'Outro'
                                        
                                    p_type = str(row.get('tipo', 'Outro'))
                                    if p_type not in utils.TIPOS: p_type = 'Outro'
                                    
                                    try:
                                        p_price = float(row.get('preco', 0))
                                        if p_price < 0: raise ValueError
                                    except:
                                        p_price = 0.0
                                        
                                    try:
                                        p_qty = int(row.get('quantidade', 0))
                                        if p_qty < 0: raise ValueError
                                    except:
                                        p_qty = 0
                                        
                                    p_exp = str(row.get('data_validade', ''))
                                    
                                    # Tentar obter o ID se existir
                                    p_id = row.get('id', None)
                                    if pd.notna(p_id):
                                        try:
                                            p_id = int(p_id)
                                        except:
                                            p_id = None
                                    else:
                                        p_id = None
                                    
                                    db.add_product(
                                        p_name,
                                        p_brand,
                                        p_style,
                                        p_type,
                                        p_price,
                                        p_qty,
                                        p_exp,
                                        None, # Imagem via CSV não suportada facilmente
                                        id=p_id
                                    )
                                    success_count += 1
                                    
                                except Exception as e_row:
                                    fail_count += 1
                                    error_log.append(f"Linha {index + 2}: {p_name if 'p_name' in locals() else 'Desconhecido'} - {e_row}")
                                
                                # Update progress
                                progress_bar.progress((index + 1) / total_rows)
                            
                            st.divider()
                            if success_count > 0:
                                st.success(f"✅ {success_count} produtos importados com sucesso!")
                            
                            if fail_count > 0:
                                st.warning(f"⚠️ {fail_count} falhas na importação.")
                                with st.expander("Ver Detalhes dos Erros"):
                                    for err in error_log:
                                        st.write(err)
                            
                            if success_count > 0:
                                st.button("Atualizar Lista", on_click=st.rerun)

                    except Exception as e:
                        st.error(f"❌ Erro crítico ao ler o arquivo CSV: {e}")
    
    
    # List/Edit/Delete
    st.subheader("Lista de Produtos")
    products_df = db.get_products()
    
    # Filters
    filter_text = st.text_input("Buscar Produto", key="search_prod")
    if not products_df.empty:
        if filter_text:
            products_df = products_df[
                products_df['name'].str.contains(filter_text, case=False, na=False) | 
                products_df['brand'].str.contains(filter_text, case=False, na=False) |
                products_df['style'].str.contains(filter_text, case=False, na=False) |
                products_df['type'].str.contains(filter_text, case=False, na=False) |
                products_df['id'].astype(str).str.contains(filter_text, case=False, na=False) |
                products_df['price'].astype(str).str.contains(filter_text, case=False, na=False) |
                products_df['quantity'].astype(str).str.contains(filter_text, case=False, na=False) |
                products_df['expiration_date'].astype(str).str.contains(filter_text, case=False, na=False)
            ]
        
        # Grid Layout with Images and Actions
        cols_per_row = 3
        rows = len(products_df)
        
        for i in range(0, rows, cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < rows:
                    row = products_df.iloc[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            # Image
                            img_src = utils.get_product_image_source(row)
                            if img_src:
                                st.image(img_src, use_container_width=True)
                            else:
                                st.markdown("*Sem Imagem*")
                                
                            st.markdown(f"**{row['name']}**")
                            st.caption(f"{row['brand']} | {row['style']}")
                            st.markdown(f"**Preço:** R$ {row['price']:.2f}")
                            st.markdown(f"**Validade:** {row['expiration_date']}")
                            st.markdown(f"**Estoque:** {row['quantity']}")
                            
                            # Actions Expander
                            with st.expander("Gerenciar"):
                                # Sale
                                st.markdown("##### Vender")
                                if row['quantity'] > 0:
                                    sell_qty = st.number_input("Qtd", min_value=1, max_value=int(row['quantity']), key=f"sell_qty_{row['id']}")
                                    if st.button("Vender", key=f"btn_sell_{row['id']}"):
                                        user_id = st.session_state['user'][0] if 'user' in st.session_state and st.session_state['user'] else None
                                        success, msg = db.register_sale(int(row['id']), sell_qty, user_id)
                                        if success:
                                            st.toast(msg, icon="✅")
                                            st.rerun()
                                        else:
                                            st.toast(msg, icon="❌")
                                else:
                                    st.warning("Esgotado")
                                
                                st.divider()
                                
                                # Edit Trigger (Store ID in session to open modal/form elsewhere or inline)
                                # Inline editing in a grid is complex. Let's use a dialog or stick to the form below.
                                # For simplicity and robustness, we can use a button to load the 'Edit Form' at the top or a dialog.
                                # Streamlit 1.23+ has st.experimental_dialog (now st.dialog). Assuming recent version.
                                # If not, we fall back to session state loading.
                                
                                if st.button("Editar / Excluir", key=f"btn_edit_{row['id']}"):
                                    st.session_state['edit_prod_id'] = int(row['id'])
                                    st.rerun()

    # Edit Modal/Section
    if 'edit_prod_id' in st.session_state:
        prod_id = st.session_state['edit_prod_id']
        action_prod = db.get_product_by_id(prod_id)
        if action_prod:
            with st.form(f"edit_prod_form_{prod_id}"):
                st.subheader(f"Editando: {action_prod[1]}")
                e_name = st.text_input("Nome", value=action_prod[1])
                
                try: b_idx = utils.MARCAS.index(action_prod[2])
                except: b_idx = 0
                e_brand = st.selectbox("Marca", utils.MARCAS, index=b_idx)
                
                try: s_idx = utils.ESTILOS.index(action_prod[3])
                except: s_idx = 0
                e_style = st.selectbox("Estilo", utils.ESTILOS, index=s_idx)
                
                try: t_idx = utils.TIPOS.index(action_prod[4])
                except: t_idx = 0
                e_type = st.selectbox("Tipo", utils.TIPOS, index=t_idx)
                
                try: e_price_val = float(action_prod[5])
                except: e_price_val = 0.0
                if e_price_val < 0.01: e_price_val = 0.01
                e_price = st.number_input("Preço", value=e_price_val, min_value=0.01)
                
                try: e_qty_val = int(action_prod[6])
                except: e_qty_val = 0
                e_qty = st.number_input("Qtd", value=e_qty_val, min_value=0, step=1)
                
                # Safe date parsing
                default_date = datetime.date.today()
                if action_prod[7]:
                    try:
                        default_date = datetime.datetime.strptime(str(action_prod[7]), "%Y-%m-%d").date()
                    except:
                        try:
                             # Try fallback format if different
                             default_date = datetime.datetime.strptime(str(action_prod[7]), "%d/%m/%Y").date()
                        except:
                            pass
                e_exp_date = st.date_input("Vencimento", value=default_date)
                
                e_image = st.file_uploader("Nova Imagem", type=['png', 'jpg', 'jpeg'])
                
                col_save, col_del, col_close = st.columns(3)
                
                with col_save:
                    if st.form_submit_button("Salvar"):
                        try:
                            img_bytes = action_prod[8]
                            if e_image:
                                img_bytes = e_image.read()
                            
                            db.update_product(prod_id, e_name, e_brand, e_style, e_type, e_price, e_qty, str(e_exp_date), img_bytes)
                            st.success("Produto atualizado!")
                            if 'edit_prod_id' in st.session_state: del st.session_state['edit_prod_id']
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar: {e}")
                
                with col_del:
                    if st.form_submit_button("EXCLUIR", type="primary"):
                        try:
                            db.delete_product(prod_id)
                            st.success("Produto excluído.")
                            if 'edit_prod_id' in st.session_state: del st.session_state['edit_prod_id']
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao excluir: {e}")
                        
                with col_close:
                    if st.form_submit_button("Cancelar"):
                        if 'edit_prod_id' in st.session_state: del st.session_state['edit_prod_id']
                        st.rerun()
        else:
             if 'edit_prod_id' in st.session_state: del st.session_state['edit_prod_id']
             st.rerun()
