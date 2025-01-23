import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO
import openpyxl  # Ensure openpyxl is installed

# Database connection
def create_db():
    conn = sqlite3.connect("ingredient.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ingredients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    quantity_per_person REAL NOT NULL,
                    unit TEXT NOT NULL,
                    category TEXT NOT NULL
                )''')
    conn.commit()
    return conn

def add_ingredient(name, quantity_per_person, unit, category):
    conn = sqlite3.connect("ingredient.db")
    c = conn.cursor()
    c.execute("INSERT INTO ingredients (name, quantity_per_person, unit, category) VALUES (?, ?, ?, ?)", 
              (name, quantity_per_person, unit, category))
    conn.commit()
    conn.close()

def get_ingredients():
    conn = sqlite3.connect("ingredient.db")
    c = conn.cursor()
    c.execute("SELECT * FROM ingredients")
    ingredients = c.fetchall()
    conn.close()
    return ingredients

def get_categories():
    conn = sqlite3.connect("ingredient.db")
    c = conn.cursor()
    c.execute("SELECT DISTINCT category FROM ingredients")
    categories = c.fetchall()
    conn.close()
    return [category[0] for category in categories]

def update_ingredient(ingredient_id, name, quantity_per_person, unit, category):
    conn = sqlite3.connect("ingredient.db")
    c = conn.cursor()
    c.execute('''UPDATE ingredients
                 SET name = ?, quantity_per_person = ?, unit = ?, category = ?
                 WHERE id = ?''', (name, quantity_per_person, unit, category, ingredient_id))
    conn.commit()
    conn.close()

def delete_ingredient(ingredient_id):
    conn = sqlite3.connect("ingredient.db")
    c = conn.cursor()
    c.execute("DELETE FROM ingredients WHERE id = ?", (ingredient_id,))
    conn.commit()
    conn.close()

# Initialize database
conn = create_db()

# Authentication system
def check_credentials(username, password):
    return username == "kitchen" and password == "chef1234"

# Streamlit app
st.title("CRISPAN Hotel Meal Preparation Manager")

# Tabs
tabs = st.tabs(["Add Ingredients", "Calculate Ingredients", "Manage Ingredients", "Ingredient Report"])

# Tab 1: Add Ingredients
with tabs[0]:
    st.header("Add Ingredients")
    with st.form("add_ingredient_form"):
        name = st.text_input("Ingredient Name")
        quantity_per_person = st.number_input("Quantity per Person", min_value=0.0, format="%f")
        unit = st.text_input("Unit of Measurement (e.g., kg, liters, cups)")
        category = st.text_input("Category (e.g., Soup, Rice, Salad)")
        submitted = st.form_submit_button("Add Ingredient")

        if submitted:
            if name and quantity_per_person and unit and category:
                add_ingredient(name, quantity_per_person, unit, category)
                st.success(f"Ingredient '{name}' added successfully!")
            else:
                st.error("Please fill out all fields.")

# Tab 2: Calculate Ingredients
with tabs[1]:
    st.header("Calculate Ingredients")
    categories = get_categories()

    if categories:
        selected_category = st.selectbox("Select Meal Category", options=categories)
        ingredients = [i for i in get_ingredients() if i[4] == selected_category]

        if ingredients:
            search_query = st.text_input("Search Ingredients")
            filtered_ingredients = [ingredient for ingredient in ingredients if search_query.lower() in ingredient[1].lower()] if search_query else ingredients

            selected_ingredients = st.multiselect(
                "Select Ingredients",
                options=[(ingredient[0], ingredient[1]) for ingredient in filtered_ingredients],
                format_func=lambda x: x[1]
            )
            total_people = st.number_input("Enter Total Number of People", min_value=1, step=1)

            if st.button("Calculate") and selected_ingredients:
                st.subheader("Total Ingredients Required")
                for ingredient_id, ingredient_name in selected_ingredients:
                    ingredient = next((i for i in ingredients if i[0] == ingredient_id), None)
                    if ingredient:
                        total_quantity = ingredient[2] * total_people
                        st.write(f"{ingredient_name}: {total_quantity:.2f} {ingredient[3]}")
            elif not selected_ingredients:
                st.warning("Please select at least one ingredient.")
        else:
            st.warning("No ingredients found for the selected category.")
    else:
        st.warning("No categories available. Please add ingredients first.")

# Tab 3: Manage Ingredients
with tabs[2]:
    st.header("Manage Ingredients")

    # Session state for login
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.subheader("Login Required")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if check_credentials(username, password):
                st.session_state.logged_in = True
                st.success("Login successful!")
            else:
                st.error("Invalid username or password.")
    else:
        st.subheader("Manage Ingredients Section")
        ingredients = get_ingredients()
        if ingredients:
            selected_ingredient = st.selectbox("Select Ingredient to Edit/Delete", options=ingredients, format_func=lambda x: x[1])
            if selected_ingredient:
                ingredient_id, name, quantity_per_person, unit, category = selected_ingredient
                with st.form("edit_ingredient_form"):
                    name = st.text_input("Ingredient Name", value=name)
                    quantity_per_person = st.number_input("Quantity per Person", min_value=0.0, format="%f", value=quantity_per_person)
                    unit = st.text_input("Unit of Measurement", value=unit)
                    category = st.text_input("Category", value=category)
                    save_changes = st.form_submit_button("Save Changes")
                    delete = st.form_submit_button("Delete Ingredient")

                    if save_changes:
                        update_ingredient(ingredient_id, name, quantity_per_person, unit, category)
                        st.success(f"Ingredient '{name}' updated successfully!")
                    elif delete:
                        delete_ingredient(ingredient_id)
                        st.success(f"Ingredient '{name}' deleted successfully!")
        else:
            st.warning("No ingredients to manage.")

# Tab 4: Ingredient Report
with tabs[3]:
    st.header("Ingredient Report")
    ingredients = get_ingredients()
    if ingredients:
        df = pd.DataFrame(ingredients, columns=["ID", "Name", "Quantity per Person", "Unit", "Category"])
        st.dataframe(df)

        # Generate Excel file dynamically
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Ingredients")
        buffer.seek(0)

        st.download_button(
            label="Download Report as Excel",
            data=buffer,
            file_name="ingredient_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Generate CSV file dynamically
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="Download Report as CSV",
            data=csv_data,
            file_name="ingredient_report.csv",
            mime="text/csv"
        )
    else:
        st.info("No ingredients available to generate a report.")