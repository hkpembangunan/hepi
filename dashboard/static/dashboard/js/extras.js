
$(document).ready(function () {
let tables = $('.datatables').each(function () {
    let table = $(this).DataTable();
    $('.enable-search th', this).each(function () {
        if ($(this).hasClass('no-search')) {
            $(this).html('');
            return;
        }
        let title = $(this).text();
        $(this).html('<input type="text" class="form-control form-control-sm" placeholder="Search ' + title + '" />');
        const val = new URLSearchParams(window.location.search).get('ts'+title.toLowerCase());
        $('input', this).val(
            val ? val : ''
        )
        table.column($(this).index()).search(val ? val : '', true, false).draw();
    });
    let counter = 0;
    let input = $('.enable-search input', this);
    table.columns().every(function () {
        let that = this;
        if (counter < input.length) {
            input.eq(counter).on('keyup change clear', function () {
                if (that.search() !== this.value) {
                    that.search(this.value).draw();
                }
            });
        }
        counter++;
    });
    
});
});
document.querySelectorAll('.warn-action').forEach((e) => {
    e.addEventListener('click', (event) => {
        event.preventDefault();
        let form = e.closest('form');
        Swal.fire({
            title: 'Are you sure?',
            text: "You won't be able to revert this!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: '<i class="fas fa-check"></i> Absolutely',
            cancelButtonText: '<i class="fas fa-times"></i> Cancel',
            reverseButtons: true,
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6c757d',
        }).then((result) => {
            if (result.isConfirmed) {
                form.submit();
            }
        }
        )
    });
});

// listen for document changes if warn-action is added dynamically
document.addEventListener('DOMNodeInserted', function (event) {
    let w_act_button = event.target.querySelector?.(".warn-action")
    if (w_act_button) {
        w_act_button.addEventListener('click', (event) => {
            event.preventDefault();
            let form = event.target.closest('form');
            Swal.fire({
                title: 'Are you sure?',
                text: "You won't be able to revert this!",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: '<i class="fas fa-check"></i> Absolutely',
                cancelButtonText: '<i class="fas fa-times"></i> Cancel',
                reverseButtons: true,
                confirmButtonColor: '#dc3545',
                cancelButtonColor: '#6c757d',
            }).then((result) => {
                if (result.isConfirmed) {
                    form.submit();
                }
            }
            )
        });
    }
});


function removeHash () { 
    var scrollV, scrollH, loc = window.location;
    var hash = window.location.hash;
    if ("pushState" in history)
        history.replaceState("", document.title, loc.pathname + loc.search);
    else {
        // Prevent scrolling by storing the page's current scroll offset
        scrollV = document.body.scrollTop;
        scrollH = document.body.scrollLeft;

        loc.hash = "";

        // Restore the scroll offset, should be flicker free
        document.body.scrollTop = scrollV;
        document.body.scrollLeft = scrollH;
    }
    if (hash) {
        var element = document.getElementById(hash.substring(1));
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
        }
    }
}

removeHash();


$(document).ready(() => {
    $('.searchable').select2();
})

// add eye icon to password fields
$('document').ready(() => {
    $('input[type=password]').each(function () {
        let el = $(this);
        // add whitespace nowrap to parent
        el.parent().css('white-space', 'nowrap');
        // add style to closest label
        el.siblings('label').css('display', 'block');
        // add style to input
        el.css('width', '100%');
        el.css('display', 'inline-block');
        // add eye icon
        el.after('<i class="fas fa-eye eye-icon" style="cursor: pointer; margin-left: -30px;"></i>');
    });
    $('.eye-icon').on('click', function () {
        let input = $(this).prev();
        if (input.attr('type') == 'text') {
            input.attr('type', 'password');
            $(this).removeClass('fa-eye-slash');
            $(this).addClass('fa-eye');
        } else {
            input.attr('type', 'text');
            $(this).removeClass('fa-eye');
            $(this).addClass('fa-eye-slash');
        }
    });
});

// encode all hrefs
$('document').ready(() => {
    $('a').each(function () {
        let href = $(this).attr('href');
        if (href) {

            href = href.replace('#', '%23');
            // change href
            $(this).attr('href', href);
        }
    });
});