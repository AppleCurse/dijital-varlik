from agentik_dongu import AgentikDongu
dongu = AgentikDongu()
s = dongu.calistir("Merhaba")
print(f"STATUS: {s['status']} | ROTA: {s['rota']} | MAHKEME: {s['mahkeme_gorev']} → {s['mahkeme_sonuc']}")
dongu.kapat()
