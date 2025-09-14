# MineServer Scout

**MineServer Scout** é uma ferramenta simples e educativa para **explorar servidores Minecraft** em um host, verificando quais portas estão ativas e coletando informações públicas como MOTD, versão, número de jogadores e ícone do servidor.  

> ⚠️ Atenção: esta ferramenta é **apenas para fins educativos**. Não use para invadir ou prejudicar servidores de terceiros. Sempre obtenha permissão antes de testar servidores que você não possui.

---

## Funcionalidades

- Escaneia um **intervalo de portas** em um host e detecta servidores Minecraft ativos.  
- Exibe informações públicas do servidor:  
  - **Porta**  
  - **Versão do servidor**  
  - **MOTD** (mensagem do servidor)  
  - **Número de jogadores online**  
  - **Ícone do servidor (favicon)**  
- Interface web moderna com:  
  - Tabela ordenável e filtrável  
  - Botão para **copiar IP completo do servidor**  
  - Feedback de status (em progresso, concluído ou erro)  
  - Loader animado durante o scan  

---

## Pré-requisitos

- Python 3.8 ou superior  
- Pacotes Python:

```bash
pip install -r requirements.txt

