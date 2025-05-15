{
    'name': 'Bitbucket Integration',
    'version': '18.0.1.0.0',
    'category': 'Extra Tools',
    'summary': 'Connect and manage Bitbucket accounts, repositories and branches',
    'description': """
This module provides integration with Bitbucket to:
- Connect Bitbucket accounts
- List and manage repositories
- Track branches and their status
- Sync repository information
    """,
    'author': 'Arkiphere Cloud',
    'website': 'https://arkiphere.cloud',
    'depends': ['base','sh_git'],
    'data': [
                
            ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'sequence': 1,
} 