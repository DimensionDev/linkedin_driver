from setuptools import find_packages, setup

setup(
    name='linkedin_driver',
    version='0.1.0',
    description='Linkedin driver.',
    url='https://github.com/sujitech/linkedin_driver',
    author='Mindey',
    author_email='mindey@qq.com',
    license='ASK FOR PERMISSIONS',
    packages = find_packages(exclude=['docs', 'tests*']),
    install_requires=['metadrive'],
    extras_require = {
        'test': ['coverage', 'pytest', 'pytest-cov'],
    },
    zip_safe=False
)
