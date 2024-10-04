# Base URLs configuration for scheduled crawling
cookies = {
    '_ym_uid': '1672401180348950566',
    'over18': '1',
    'list_mode': 'h',
    '_ym_d': '1719802344',
    'theme': 'light',
             'locale': 'zh',
             'comment_warning': '1',
             '_ym_isad': '1',
             'cf_clearance': 'NEbGQtoKGMc30VjpG6V2Diw_CW6OFxkhJRi.4nX8aCw-1727197902-1.2.1.1-xcAacenoiC3QbIM7gqnKUjhnu4Q0j3aB6w9AE42eMwh0Zc1fPmeu1J2ajMrChZcqYdYIJ7Qtqf5Ap1aYxnnuFFA0bwYZa_tpTv8ivZSQPEfLl80VZ786yLMWlYl7sYxFoPoRAh3PiCF__04p3VA0IRjM.khSOK2WNjTWSIbHlIjJs8W22HoKpRJdU_drm0rV_fnAA7X5Iq5LxTq_v6wpt0GjaiHGZckEQNMiJq4T4Rmb0T0h5o.pxvep5R6jiyalbGyAoHYt1fTdARUS7vhlM7zVwj1NKue_PObRED57GzLc8OX9oXcRqS5z1wEyPf5zFQ64Sc1qUDIATgopQvR.Kzk0LYZasZWLq0jrliaHpMHtKCI63y2_EKUiRIH5gzQ6kcqgZYKMVM0X9HcEOcaKpg',
             '_jdb_session': 'SS830WZLXHYHb9mdHadcLcR8NIpB3qF8fzey2VwbWgHp%2Bb%2FSHm%2BR4INnbSusQVuugCml3vqzH5agGJq8%2BVdtorF6%2Bzmn7NlHTVsCv0IYmRFwzMbptXHjJrx%2Fc2U3nb1SF0vLYx3bGlnGB7wX%2FxJtDDJ%2FBUSaofFEgCgbUsr2FOVIH9uWI3xuZEVbL6U1x%2FtaEuthLMBoNF8qmNwEnoZUZ3OEWmhlZqhojMSqzGMLvFfHaRouDQ8%2F2CPaoEukQADUnFYSaoEEuEoCexh1euzhdp7T5zmYaChDvtMn5DQlQ1OlAACQh6JQ83BKONiWrOJBN64mQj%2Fny6IUfeGsL7KW0%2BU8RaqeClCEzCCli1O4Q1UAGCGQAB%2B8bGq70mGLrtsasIpo3JyT3JGo4W4z%2BbKsNa2nGjm%2BAV19P4bB0fFu7khNmCSD3cDl0EipkOpXnqIX4X8mlwqTApilp5K1BQ6tNzkr--%2FlX5QajwWm9f5Mfr--DlWUXgDCQb0lJjGxDJ0U%2FQ%3D%3D',
}

base_urls = {
    'makers': [
        'zK', 'Y46', '6M', 'ZXX', 'rmZ', 'bgA', '35e', 'Ywz', '333', 'Ww7',
        'p3k', '8Xd', 'Aby', 'J2x', '89V', '5458', 'kBvm', 'M6A', '725b'
    ],
    'series': ['ynPA'],
    'video_codes': [
        'SONE', 'TPPN', 'AUKG', 'REBD', 'CJOD', 'KBR', 'MOGI', 'STARS', 'START',
        'HDKA', 'REBDB', 'MVSD', 'dass', 'suwk', 'SQTE', 'MOPT', 'BBAN', 'HSODA',
        'MAAN', 'PFES'
    ]
}


def generate_full_urls():
    full_urls = []
    for category, codes in base_urls.items():
        for code in codes:
            url = f'https://javdb.com/{category}/{code}'
            full_urls.append((url, 1))
    return full_urls


# Generate the full URLs for scheduled crawling
scheduled_urls = generate_full_urls()

# Temporary URLs for manual crawling (empty by default)
temp_urls = []
