# Modelo de segurança

- Não armazene credenciais em YAML, exemplos ou linha de comando.
- Use variáveis de ambiente ou o cofre local; proteja a senha mestra em um
  gerenciador corporativo.
- Inventário e captura só podem ser usados em redes formalmente autorizadas.
- O honeypot deve ficar isolado, sem credenciais verdadeiras e sem acesso de
  saída privilegiado.
- Revise diffs de configuração e planos de IaC antes de executar mudanças.
- Dados anonimizados por máscara ainda podem ser pessoais; pseudonimização não
  equivale automaticamente a anonimização irreversível para fins legais.
- Faça rotação das chaves usadas para pseudonimização de acordo com a política
  de retenção e preserve-as somente quando a correlação histórica for necessária.
