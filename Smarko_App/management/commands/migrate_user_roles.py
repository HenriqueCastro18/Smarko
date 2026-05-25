from django.core.management.base import BaseCommand
from firebase_admin import firestore

class Command(BaseCommand):
    help = 'Migrate user roles in Firestore - adds role=user to all users, role=developer to HenriqueCastro'

    def handle(self, *args, **options):
        try:
            db = firestore.client()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao conectar ao Firestore: {e}'))
            return

        self.stdout.write(self.style.WARNING('[INFO] Iniciando migracao de roles no Firestore...'))

        try:
            perfis_ref = db.collection('perfis')
            docs = perfis_ref.stream()

            users_updated = 0
            users_no_role = 0
            dev_updated = 0
            docs_list = list(docs)

            for doc in docs_list:
                doc_data = doc.to_dict()
                username = doc_data.get('username', '')
                existing_role = doc_data.get('role')

                if not existing_role:
                    users_no_role += 1

                    if username == 'HenriqueCastro':
                        perfis_ref.document(doc.id).update({'role': 'developer'})
                        self.stdout.write(
                            self.style.SUCCESS(f'[OK] {username}: role definido como "developer"')
                        )
                        dev_updated += 1
                    else:
                        perfis_ref.document(doc.id).update({'role': 'user'})
                        self.stdout.write(
                            self.style.SUCCESS(f'[OK] {username}: role definido como "user"')
                        )
                        users_updated += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n[SUCCESS] Migracao concluida!\n'
                    f'   - Usuarios com role="user": {users_updated}\n'
                    f'   - Usuarios com role="developer": {dev_updated}\n'
                    f'   - Total atualizado: {users_updated + dev_updated}\n'
                    f'   - Usuarios que ja tinham role: {len(docs_list) - users_no_role}'
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro durante migracao: {e}'))
