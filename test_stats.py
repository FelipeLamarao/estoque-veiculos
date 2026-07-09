import pandas as pd
import os
from test_loader import load_data_fixed

df1 = load_data_fixed('estoque.csv')
df2 = load_data_fixed('Rel_MalaDireta - 2026-06-30T114259.554.xls')

print("Estoque shape:", df1.shape)
print("Progresso shape:", df2.shape)

print("\nEstoque - Situação counts:")
print(df1['Situação'].value_counts())
print("\nProgresso - Situação counts:")
print(df2['Situação'].value_counts())

print("\nEstoque - Preço stats:")
print(df1['Preço'].describe())
print("\nProgresso - Preço stats:")
print(df2['Preço'].describe())

print("\nEstoque - Dias estoque stats:")
print(df1['Dias estoque'].describe())
print("\nProgresso - Dias estoque stats:")
print(df2['Dias estoque'].describe())
