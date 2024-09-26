document.addEventListener('click', click);

function click(e) {
  let el;

  el = e.target;

  if (el !== e.currentTarget) {
    if (el.nodeName === 'BUTTON') {

      if (el.classList.contains('is-active')) {
        el.classList.remove('is-active');
      } else {
        el.classList.add('is-active');
      }
    }
  }
  event.stopPropagation();
}