COMERCIAL BELA VISTA — SISTEMA PROFISSIONAL — WINDOWS 10/11

USO PELO CLIENTE
1. Copie instalar_sistema.exe para uma pasta onde o usuário possa gravar arquivos.
2. Abra instalar_sistema.exe.
3. No primeiro acesso, use o login inicial abaixo.

O banco supermercado.db e as pastas recibos e relatorios são criados ao lado do
executável. Faça cópias de segurança periódicas desses arquivos. Não execute o
programa diretamente de uma pasta protegida, como Arquivos de Programas.

LOGIN INICIAL
Usuário: admin
Senha: admin123

IMPORTANTE: troque a senha inicial e cadastre funcionários com senhas próprias.
A senha é armazenada como hash, não em texto simples.

GERAR O EXECUTÁVEL (WINDOWS)
Com Python 3.10 ou superior instalado, abra o Prompt de Comando nesta pasta e
execute:
   py -m pip install -r requirements.txt
   py -m pip install pyinstaller
   py -m PyInstaller --clean --onefile --windowed --name instalar_sistema --add-data "assets\carrinho_compras.png;assets" main.py

O arquivo instalar_sistema.exe será criado em:
   dist\instalar_sistema.exe

RECURSOS
- Cadastro de produtos: código/barras, nome, custo, imposto, lucro, preço calculado e estoque.
- Entrada de estoque e baixa automática ao finalizar a venda.
- Carrinho de compras e formas de pagamento dinheiro, débito, crédito e Pix.
- Pagamento em dinheiro com cálculo de restante e troco.
- Histórico de vendas e consulta de itens.
- Relatórios mensais em PDF e Excel.
- Perfis gerente/caixa; apenas gerente vê a aba Funcionários.
- Recibo PDF de cada venda.
- Scanner USB: a maioria funciona como teclado; clique no campo Código e leia o produto.
- Atalhos: F1 cancela toda a compra após confirmação; F2 remove o produto selecionado; F3 foca o campo do código; F4 abre o pagamento; F5 inicia o próximo cliente; Esc volta da tela de pagamento à compra sem finalizá-la; 1–4 selecionam pagamento quando não se está digitando nos campos do caixa.

GERAR EXE
Dentro da pasta do projeto, execute:
   py -m pip install pyinstaller
   py -m PyInstaller --onefile --windowed --name Supermercado --add-data "assets\carrinho_compras.png;assets" main.py

O executável estará em:
   dist\Supermercado.exe

OBSERVAÇÕES IMPORTANTES
- O banco supermercado.db será criado automaticamente ao executar o programa.
- Faça cópias de segurança periódicas do arquivo supermercado.db.
- A fórmula de preço de venda é uma regra simplificada: custo + percentual de imposto sobre o custo + percentual de lucro sobre o custo. Ajuste-a às regras contábeis/fiscais do seu negócio.
- O pagamento por débito, crédito e Pix é registrado após confirmação manual. Este programa não se conecta a bancos, adquirentes ou sistemas fiscais.
- Antes de usar em um supermercado real, teste cuidadosamente e solicite revisão profissional, especialmente para tributação, emissão fiscal, LGPD, segurança e integração com pagamentos.
- O leitor USB é compatível com scanners que digitam o código como se fosse teclado. Leitura por câmera não está incluída nesta versão.
