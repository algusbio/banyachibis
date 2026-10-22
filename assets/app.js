/* No dependencies, trackers or external scripts. */
document.documentElement.classList.remove('no-js');

const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('.nav');
function closeMenu() {
  navigation.classList.remove('is-open');
  menuButton.setAttribute('aria-expanded', 'false');
  menuButton.setAttribute('aria-label', 'Открыть меню');
}
menuButton.addEventListener('click', () => {
  const open = menuButton.getAttribute('aria-expanded') !== 'true';
  navigation.classList.toggle('is-open', open);
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
});
navigation.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
document.addEventListener('keydown', event => { if (event.key === 'Escape') closeMenu(); });
document.addEventListener('click', event => {
  if (!navigation.contains(event.target) && !menuButton.contains(event.target)) closeMenu();
});
matchMedia('(min-width: 1051px)').addEventListener('change', closeMenu);

const photos = [...document.querySelectorAll('.photo')];
const filters = [...document.querySelectorAll('.filter')];
const moreButton = document.querySelector('#show-photos');
const count = document.querySelector('#gallery-count');
let activeFilter = 'all';
let expanded = false;
function updateGallery() {
  let visible = 0;
  photos.forEach((photo, index) => {
    const matches = activeFilter === 'all' || photo.dataset.category === activeFilter;
    const show = matches && (activeFilter !== 'all' || expanded || index < 6);
    photo.hidden = !show;
    photo.classList.toggle('is-visible', show);
    if (show) visible++;
  });
  filters.forEach(button => {
    const selected = button.dataset.filter === activeFilter;
    button.classList.toggle('active', selected);
    button.setAttribute('aria-pressed', String(selected));
  });
  count.textContent = `Показано ${visible} из ${photos.length} фотографий`;
  moreButton.hidden = activeFilter !== 'all';
  moreButton.setAttribute('aria-expanded', String(expanded));
  moreButton.innerHTML = expanded ? 'Свернуть галерею <span aria-hidden="true">−</span>' : `Все ${photos.length} фотографий <span aria-hidden="true">+</span>`;
}
filters.forEach(button => button.addEventListener('click', () => {
  activeFilter = button.dataset.filter;
  updateGallery();
}));
moreButton.addEventListener('click', () => {
  expanded = !expanded;
  updateGallery();
  if (!expanded) document.querySelector('#gallery').scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'});
});
updateGallery();

const lightbox = document.querySelector('#lightbox');
const lightboxImage = document.querySelector('#lightbox-image');
const lightboxCaption = document.querySelector('#lightbox-caption');
let selected = 0;
let currentPhotos = [];
let previousFocus;
function showPhoto(index) {
  selected = (index + currentPhotos.length) % currentPhotos.length;
  const photo = currentPhotos[selected];
  const image = photo.querySelector('img');
  lightboxImage.src = photo.href;
  lightboxImage.alt = image.alt;
  lightboxCaption.textContent = photo.dataset.caption;
  document.querySelector('#lightbox-count').textContent = `${selected + 1} / ${currentPhotos.length}`;
}
photos.forEach(photo => photo.addEventListener('click', event => {
  if (!lightbox.showModal || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  previousFocus = photo;
  currentPhotos = photos.filter(item => activeFilter === 'all' || item.dataset.category === activeFilter);
  showPhoto(currentPhotos.indexOf(photo));
  lightbox.showModal();
  document.body.classList.add('modal-open');
  lightbox.querySelector('.lightbox-close').focus();
}));
lightbox.querySelector('.lightbox-close').addEventListener('click', () => lightbox.close());
lightbox.querySelector('.lightbox-prev').addEventListener('click', () => showPhoto(selected - 1));
lightbox.querySelector('.lightbox-next').addEventListener('click', () => showPhoto(selected + 1));
lightbox.addEventListener('click', event => { if (event.target === lightbox) lightbox.close(); });
lightbox.addEventListener('close', () => {
  document.body.classList.remove('modal-open');
  previousFocus?.focus({preventScroll: true});
});
lightbox.addEventListener('keydown', event => {
  if (event.key === 'ArrowRight') { event.preventDefault(); showPhoto(selected + 1); }
  if (event.key === 'ArrowLeft') { event.preventDefault(); showPhoto(selected - 1); }
});
let touchStart;
lightboxImage.addEventListener('touchstart', event => {
  if (event.touches.length === 1) touchStart = {x: event.touches[0].clientX, y: event.touches[0].clientY};
  else touchStart = null;
}, {passive: true});
lightboxImage.addEventListener('touchend', event => {
  if (!touchStart || event.changedTouches.length !== 1) return;
  const dx = event.changedTouches[0].clientX - touchStart.x;
  const dy = event.changedTouches[0].clientY - touchStart.y;
  if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) showPhoto(selected + (dx < 0 ? 1 : -1));
  touchStart = null;
}, {passive: true});
