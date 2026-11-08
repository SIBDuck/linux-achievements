pkgname=python-linux-achievements
_name=${pkgname#python-}
pkgver=1.0.0
pkgrel=1
pkgdesc="The utility adding achievements into your GNU/Linux system!"
arch=('any')
url="https://github.com/SIBDuck/linux-achievements"
license=('AGPL-3.0-or-later')
depends=('python' 'python-watchdog' 'python-psutil')
makedepends=('python-build' 'python-installer' 'python-wheel' 'python-setuptools')
source=("achievement_manager" "config" "pyproject.toml" "config_shrc" "data")
sha256sums=('SKIP' 'SKIP' 'SKIP' 'SKIP' 'SKIP')
build(){
    cd "${srcdir}"
    python -m build --wheel --no-isolation
}
package(){
    cd "${srcdir}"
    python -m installer --destdir="$pkgdir" dist/*.whl
}
