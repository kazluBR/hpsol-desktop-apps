# Aplicações Desktop em Python

Aplicações desenvolvidas para o Hotel Pousada do Sol que se comunicam diretamente com o banco de dados firebase do sistema principal através de VPN.

## Passos iniciais

- Criar ambiente virtual: `python -m venv _env`
- Ativar ambiente: `./_env/Scripts/Activate.ps1`
- Atualizar pip: `python -m pip install --upgrade pip`
- Instalar todos os pacotes: `pip install -r requirements.txt`
- Executar app: `./{app_name} python main.py`

## Outros comandos

- Atualizar requirements.txt após instalar novos pacotes: `pip freeze > requirements.txt`
- Atualizar UI após modificar interface.ui: `./{app_name} pyuic5 -o interface.py interface.ui`
- Gerar executável do app (exe dentro da pasta dist): `./{app_name} pyinstaller -F -w main.py`

## Aplicativos

- [A&B](/a&b): Comparativo de receitas por pontos de venda.
- [Aniversariantes](/aniversariantes): Listagem dos aniversariantes por dia.
- [Despesas](/despesas): Comparativo de despesas por grupos financeiros.
- [Diarias](/diarias): Comparativo de diárias dos hotéis na Booking por período.
- [Receitas](/receitas): Comparativo de receitas por histórico.
- [Reservas](/reservas): Comparativo de reservas por origem.
- [SaldosEstoque](/saldos estoque): Listagem de saldos atuais dos itens por estoque.
- [TarifaFacil](/tarifa facil): Exibe as melhores tarifas de todas as classes de apartamento por período para auxiliar na venda direta.
- [Termometro](/termometro): Comparativo de resultados (despesas x receitas) por mês ou semestre.
