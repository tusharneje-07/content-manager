/* Content Manager — vanilla JS interactions.
   Modals, posted flow, copy image, previews, toasts. No frameworks. */
(function () {
  'use strict';

  /* ---------------------------------------------------------------- toasts */

  var toastTimer = null;

  function toast(message, isError) {
    var el = document.getElementById('toast');
    if (!el) return;
    var panel = el.querySelector('[data-toast-panel]');
    panel.textContent = message;
    panel.classList.toggle('text-red-300', Boolean(isError));
    panel.classList.toggle('text-white', !isError);
    panel.classList.toggle('text-ink', !isError);
    el.classList.remove('hidden');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      el.classList.add('hidden');
    }, 4000);
  }

  /* ------------------------------------------------- flash message banners */

  function removeFlash(el) {
    el.classList.add('opacity-0');
    setTimeout(function () { el.remove(); }, 300);
  }

  document.querySelectorAll('[data-flash]').forEach(function (el) {
    var timer = setTimeout(function () { removeFlash(el); }, 5000);
    var close = el.querySelector('[data-flash-close]');
    if (close) {
      close.addEventListener('click', function () {
        clearTimeout(timer);
        removeFlash(el);
      });
    }
  });

  /* ------------------------------------------------------ date pickers */

  function parseDate(value) {
    var match = /^([0-9]{4})-([0-9]{2})-([0-9]{2})$/.exec(value || '');
    if (!match) return null;
    var date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
    return date.getFullYear() === Number(match[1]) && date.getMonth() === Number(match[2]) - 1 && date.getDate() === Number(match[3]) ? date : null;
  }

  function dateValue(date) {
    return date.getFullYear() + '-' + String(date.getMonth() + 1).padStart(2, '0') + '-' + String(date.getDate()).padStart(2, '0');
  }

  function dateLabel(date) {
    return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric' }).format(date);
  }

  document.querySelectorAll('[data-date-picker]').forEach(function (picker) {
    var display = picker.querySelector('[data-date-display]');
    var valueInput = picker.querySelector('[data-date-value-input]');
    var popover = picker.querySelector('[data-date-popover]');
    var monthLabel = picker.querySelector('[data-date-month]');
    var days = picker.querySelector('[data-date-days]');
    var selected = parseDate(picker.dataset.dateValue);
    var view = selected ? new Date(selected.getFullYear(), selected.getMonth(), 1) : new Date(new Date().getFullYear(), new Date().getMonth(), 1);

    function updateValue(date) {
      selected = date;
      valueInput.value = date ? dateValue(date) : '';
      display.value = date ? dateLabel(date) : '';
    }

    function render() {
      monthLabel.textContent = new Intl.DateTimeFormat(undefined, { month: 'long', year: 'numeric' }).format(view);
      days.innerHTML = '';
      var firstDay = new Date(view.getFullYear(), view.getMonth(), 1).getDay();
      var lastDate = new Date(view.getFullYear(), view.getMonth() + 1, 0).getDate();
      for (var cell = 0; cell < 42; cell += 1) {
        var day = cell - firstDay + 1;
        var button = document.createElement('button');
        button.type = 'button';
        button.className = 'flex h-9 items-center justify-center rounded-lg font-mono text-code transition';
        if (day < 1 || day > lastDate) {
          button.disabled = true;
          button.classList.add('invisible');
        } else {
          var date = new Date(view.getFullYear(), view.getMonth(), day);
          button.textContent = day;
          button.dataset.date = dateValue(date);
          button.classList.add('text-body', 'hover:bg-white/[0.08]', 'hover:text-white');
          if (selected && dateValue(selected) === button.dataset.date) {
            button.classList.remove('text-body');
            button.classList.add('bg-primary', 'text-white');
          }
          button.addEventListener('click', function () {
            updateValue(parseDate(this.dataset.date));
            close();
          });
        }
        days.appendChild(button);
      }
    }

    function close() {
      popover.classList.add('hidden');
      picker.querySelector('[data-date-toggle]').setAttribute('aria-expanded', 'false');
    }

    function open() {
      document.querySelectorAll('[data-date-popover]').forEach(function (other) {
        if (other !== popover) other.classList.add('hidden');
      });
      render();
      popover.classList.remove('hidden');
      picker.querySelector('[data-date-toggle]').setAttribute('aria-expanded', 'true');
    }

    picker.querySelector('[data-date-toggle]').addEventListener('click', function () {
      if (popover.classList.contains('hidden')) open(); else close();
    });
    display.addEventListener('click', open);
    picker.querySelector('[data-date-prev]').addEventListener('click', function () {
      view.setMonth(view.getMonth() - 1);
      render();
    });
    picker.querySelector('[data-date-next]').addEventListener('click', function () {
      view.setMonth(view.getMonth() + 1);
      render();
    });
    picker.querySelector('[data-date-clear]').addEventListener('click', function () {
      updateValue(null);
      close();
    });
    picker.querySelector('[data-date-today]').addEventListener('click', function () {
      var today = new Date();
      view = new Date(today.getFullYear(), today.getMonth(), 1);
      updateValue(today);
      close();
    });
    updateValue(selected);
    render();
  });

  document.querySelectorAll('[data-sort-picker]').forEach(function (picker) {
    var toggle = picker.querySelector('[data-sort-toggle]');
    var menu = picker.querySelector('[data-sort-menu]');
    var valueInput = picker.querySelector('[data-sort-value-input]');
    var label = picker.querySelector('[data-sort-label]');
    var chevron = picker.querySelector('[data-sort-chevron]');
    var labels = { az: 'A-Z', za: 'Z-A' };

    function close() {
      menu.classList.add('hidden');
      toggle.setAttribute('aria-expanded', 'false');
      chevron.classList.remove('rotate-180');
    }

    function open() {
      document.querySelectorAll('[data-sort-menu]').forEach(function (other) {
        if (other !== menu) other.classList.add('hidden');
      });
      menu.classList.remove('hidden');
      toggle.setAttribute('aria-expanded', 'true');
      chevron.classList.add('rotate-180');
    }

    function update(value) {
      valueInput.value = value;
      label.textContent = labels[value] || labels.az;
      picker.querySelectorAll('[data-sort-option]').forEach(function (option) {
        var selected = option.dataset.sortOptionValue === value;
        option.setAttribute('aria-selected', selected ? 'true' : 'false');
        option.classList.toggle('bg-primary/10', selected);
        option.classList.toggle('text-white', selected);
        option.querySelector('[data-sort-check]').classList.toggle('hidden', !selected);
      });
    }

    toggle.addEventListener('click', function () {
      if (menu.classList.contains('hidden')) open(); else close();
    });
    picker.querySelectorAll('[data-sort-option]').forEach(function (option) {
      option.addEventListener('click', function () {
        update(option.dataset.sortOptionValue);
        close();
      });
    });
    update(picker.dataset.sortValue || 'az');
  });

  document.addEventListener('click', function (e) {
    if (!e.target.closest('[data-date-picker]')) {
      document.querySelectorAll('[data-date-popover]').forEach(function (popover) { popover.classList.add('hidden'); });
      document.querySelectorAll('[data-date-toggle]').forEach(function (toggle) { toggle.setAttribute('aria-expanded', 'false'); });
    }
    if (!e.target.closest('[data-sort-picker]')) {
      document.querySelectorAll('[data-sort-menu]').forEach(function (menu) { menu.classList.add('hidden'); });
      document.querySelectorAll('[data-sort-toggle]').forEach(function (toggle) { toggle.setAttribute('aria-expanded', 'false'); });
      document.querySelectorAll('[data-sort-chevron]').forEach(function (chevron) { chevron.classList.remove('rotate-180'); });
    }
  });

  /* ---------------------------------------------------------------- modals */

  function openModal(id) {
    var modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.remove('hidden');
    modal.classList.add('flex');
  }

  function resetSteps(modal) {
    modal.querySelectorAll('[data-step]').forEach(function (step) {
      step.classList.toggle('hidden', step.dataset.step !== 'confirm');
    });
  }

  function closeModal(id) {
    var modal = document.getElementById(id);
    if (!modal || modal.classList.contains('hidden')) return;
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    resetSteps(modal);
    modal.dispatchEvent(new CustomEvent('modal:closed'));
  }

  function showStep(modal, name) {
    modal.querySelectorAll('[data-step]').forEach(function (step) {
      step.classList.toggle('hidden', step.dataset.step !== name);
    });
    var focusable = modal.querySelector('[data-step="' + name + '"] input');
    if (focusable) focusable.focus();
  }

  function anyModalOpen() {
    return Array.prototype.some.call(document.querySelectorAll('[data-modal]'), function (m) {
      return !m.classList.contains('hidden');
    });
  }

  document.addEventListener('click', function (e) {
    var opener = e.target.closest('[data-delete-open]');
    if (opener) { openModal('delete-modal'); return; }

    var postedOpener = e.target.closest('[data-posted-detail-open]');
    if (postedOpener) { openModal('posted-modal'); return; }

    var next = e.target.closest('[data-step-next]');
    if (next) { showStep(next.closest('[data-modal]'), next.dataset.stepNext); return; }

    var back = e.target.closest('[data-step-back]');
    if (back) { showStep(back.closest('[data-modal]'), back.dataset.stepBack); return; }

    var closeBtn = e.target.closest('[data-modal-close]');
    if (closeBtn) { closeModal(closeBtn.closest('[data-modal]').id); return; }

    if (e.target.matches('[data-modal]')) closeModal(e.target.id); // backdrop click
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      document.querySelectorAll('[data-modal]').forEach(function (m) { closeModal(m.id); });
      document.querySelectorAll('[data-date-popover]').forEach(function (popover) { popover.classList.add('hidden'); });
      document.querySelectorAll('[data-sort-menu]').forEach(function (menu) { menu.classList.add('hidden'); });
      return;
    }
    /* "N" opens the Add Post page, Raycast-style */
    if (e.key.toLowerCase() === 'n' && !e.metaKey && !e.ctrlKey && !e.altKey) {
      var active = document.activeElement;
      if (active && (['INPUT', 'TEXTAREA', 'SELECT'].indexOf(active.tagName) !== -1 || active.isContentEditable)) return;
      if (anyModalOpen()) return;
      var link = document.getElementById('nav-add-link');
      if (link && window.location.pathname.indexOf('/add') === -1) window.location.href = link.href;
    }
  });

  /* ------------------------------------- posted flow on add/edit forms */

  document.querySelectorAll('form[data-posted-form]').forEach(function (form) {
    var postedCheckbox = form.querySelector('#is_posted');
    var urlField = form.querySelector('#post_url');
    var modal = document.getElementById('posted-modal');
    if (!postedCheckbox || !urlField || !modal) return;

    var saveBtn = modal.querySelector('[data-modal-url-save]');
    var modalUrlInput = modal.querySelector('[data-modal-url-input]');
    var modalUrlError = modal.querySelector('[data-modal-url-error]');
    var bypass = false;

    form.addEventListener('submit', function (e) {
      if (bypass) return;
      if (postedCheckbox.checked && !urlField.value.trim()) {
        e.preventDefault();
        openModal('posted-modal');
      }
    });

    if (saveBtn && modalUrlInput) {
      saveBtn.addEventListener('click', function () {
        var value = modalUrlInput.value.trim();
        if (!/^https?:\/\/\S+$/i.test(value)) {
          modalUrlError.textContent = 'Enter a valid URL starting with http:// or https://';
          modalUrlInput.focus();
          return;
        }
        modalUrlError.textContent = '';
        urlField.value = value;
        bypass = true;
        closeModal('posted-modal');
        form.submit();
      });
      modalUrlInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') { e.preventDefault(); saveBtn.click(); }
      });
    }

    modal.addEventListener('modal:closed', function () {
      if (!bypass) {
        postedCheckbox.checked = false; /* cancelled → do not mark as posted */
      }
      bypass = false;
      if (modalUrlInput) modalUrlInput.value = '';
      if (modalUrlError) modalUrlError.textContent = '';
    });
  });

  /* ------------------------------------------------------- copy image button */

  async function copyImageToClipboard(url, btn) {
    if (!(navigator.clipboard && window.ClipboardItem)) {
      toast('Copying images to the clipboard is not supported in this browser — use Download Image instead.', true);
      return;
    }
    var original = btn.innerHTML;
    btn.disabled = true;
    btn.style.opacity = '0.6';
    try {
      var response = await fetch(url);
      if (!response.ok) throw new Error('fetch failed');
      var blob = await response.blob();
      var bitmap = await createImageBitmap(blob);
      var canvas = document.createElement('canvas');
      canvas.width = bitmap.width;
      canvas.height = bitmap.height;
      canvas.getContext('2d').drawImage(bitmap, 0, 0);
      var png = await new Promise(function (resolve, reject) {
        canvas.toBlob(function (b) { b ? resolve(b) : reject(new Error('encode failed')); }, 'image/png');
      });
      await navigator.clipboard.write([new ClipboardItem({ 'image/png': png })]);
      toast('Image copied to clipboard.');
    } catch (err) {
      toast('Could not copy the image to the clipboard — use Download Image instead.', true);
    } finally {
      btn.disabled = false;
      btn.style.opacity = '';
      btn.innerHTML = original;
    }
  }

  document.querySelectorAll('[data-copy-media]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      copyImageToClipboard(btn.dataset.copyMedia, btn);
    });
  });

  /* ------------------------------------------------ add-form media preview */

  var fileInput = document.getElementById('media');
  var preview = document.querySelector('[data-media-preview]');
  if (fileInput && preview) {
    var objectUrls = [];
    fileInput.addEventListener('change', function () {
      objectUrls.forEach(function (url) { URL.revokeObjectURL(url); });
      objectUrls = [];
      preview.innerHTML = '';
      var files = Array.prototype.slice.call(fileInput.files || []);
      if (!files.length) { preview.classList.add('hidden'); return; }

      var grid = document.createElement('div');
      grid.className = 'grid grid-cols-2 gap-3 p-3 sm:grid-cols-3';
      files.forEach(function (file) {
        var objectUrl = URL.createObjectURL(file);
        objectUrls.push(objectUrl);
        var card = document.createElement('div');
        card.className = 'min-w-0';
        var isImage = file.type.indexOf('image/') === 0 || /\.(jpg|jpeg|png|webp|gif)$/i.test(file.name);
        var isVideo = file.type.indexOf('video/') === 0 || /\.(mp4|mov|webm|mkv)$/i.test(file.name);
        if (isImage) {
          var img = document.createElement('img');
          img.src = objectUrl;
          img.alt = 'Selected media preview';
          img.className = 'h-32 w-full rounded-lg object-cover';
          card.appendChild(img);
        } else if (isVideo) {
          var video = document.createElement('video');
          video.src = objectUrl;
          video.controls = true;
          video.muted = true;
          video.playsInline = true;
          video.className = 'h-32 w-full rounded-lg object-cover';
          card.appendChild(video);
        }
        var label = document.createElement('p');
        label.className = 'mt-1 truncate font-mono text-code text-dark-body';
        label.textContent = file.name;
        card.appendChild(label);
        grid.appendChild(card);
      });
      preview.appendChild(grid);
      preview.classList.remove('hidden');
    });
  }

  /* ----------------------------------------- YouTube song title lookup */

  function youtubeUrlFromText(value) {
    var match = /(https?:\/\/[^\s]+)/i.exec(value || '');
    if (!match) return null;
    var url = match[1].replace(/[.,!?;:)]+$/, '');
    try {
      var hostname = (new URL(url)).hostname.toLowerCase();
      if (hostname === 'youtu.be' || hostname === 'youtube.com' || hostname.endsWith('.youtube.com')) return url;
    } catch (err) {
      return null;
    }
    return null;
  }

  document.querySelectorAll('[data-youtube-song-form]').forEach(function (form) {
    var songInput = form.querySelector('[data-youtube-song-input]');
    var saveButton = form.querySelector('[data-youtube-save]');
    var preview = form.querySelector('[data-youtube-preview]');
    var title = form.querySelector('[data-youtube-preview-title]');
    var error = form.querySelector('[data-youtube-preview-error]');
    if (!songInput || !saveButton || !preview || !title || !error) return;

    var timer = null;
    var requestId = 0;
    var readyUrl = null;
    var saveLabel = saveButton.textContent;

    function setPreviewState(message, isError) {
      preview.classList.remove('hidden');
      title.textContent = isError ? '' : message;
      error.textContent = isError ? message : '';
      title.parentElement.classList.toggle('hidden', isError);
    }

    function refreshYoutubeTitle() {
      var url = youtubeUrlFromText(songInput.value);
      readyUrl = null;
      if (!url) {
        saveButton.disabled = false;
        saveButton.textContent = saveLabel;
        preview.classList.add('hidden');
        return;
      }

      requestId += 1;
      var request = requestId;
      saveButton.disabled = true;
      saveButton.textContent = 'Fetching title...';
      setPreviewState('Fetching YouTube title...', false);
      clearTimeout(timer);
      timer = window.setTimeout(function () {
        fetch('/youtube/metadata?url=' + encodeURIComponent(url), { headers: { 'X-Requested-With': 'fetch' } })
          .then(function (response) {
            return response.json().then(function (data) {
              if (!response.ok) throw new Error(data.error || 'The YouTube title could not be fetched.');
              return data;
            });
          })
          .then(function (data) {
            if (request !== requestId || youtubeUrlFromText(songInput.value) !== url) return;
            readyUrl = url;
            setPreviewState(data.title, false);
            saveButton.disabled = false;
            saveButton.textContent = saveLabel;
          })
          .catch(function (fetchError) {
            if (request !== requestId || youtubeUrlFromText(songInput.value) !== url) return;
            setPreviewState(fetchError.message, true);
            saveButton.disabled = true;
            saveButton.textContent = 'YouTube title required';
          });
      }, 350);
    }

    songInput.addEventListener('input', refreshYoutubeTitle);
    form.addEventListener('submit', function (event) {
      var url = youtubeUrlFromText(songInput.value);
      if (url && readyUrl !== url) {
        event.preventDefault();
        refreshYoutubeTitle();
      }
    });
    refreshYoutubeTitle();
  });

  /* Apply library filters without moving the filter bar or reloading the shell. */
  var libraryFilterForm = document.querySelector('[data-library-filter-form]');
  var libraryResults = document.querySelector('[data-library-results]');
  if (libraryFilterForm && libraryResults) {
    var filterSubmit = libraryFilterForm.querySelector('[data-filter-submit]');
    var libraryCount = document.querySelector('[data-library-count]');

    function applyLibraryFilters(url, pushState) {
      if (filterSubmit) {
        filterSubmit.disabled = true;
        filterSubmit.textContent = 'Applying...';
      }
      return fetch(url, { headers: { 'X-Requested-With': 'fetch' } })
        .then(function (response) {
          if (!response.ok) throw new Error('filter request failed');
          return response.text();
        })
        .then(function (html) {
          var nextDocument = new DOMParser().parseFromString(html, 'text/html');
          var nextResults = nextDocument.querySelector('[data-library-results]');
          var nextCount = nextDocument.querySelector('[data-library-count]');
          if (!nextResults) throw new Error('filter results missing');
          libraryResults.replaceWith(nextResults);
          libraryResults = nextResults;
          if (libraryCount && nextCount) libraryCount.innerHTML = nextCount.innerHTML;
          if (pushState) window.history.pushState({}, '', url);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        })
        .catch(function () {
          window.location.assign(url);
        })
        .finally(function () {
          if (filterSubmit) {
            filterSubmit.disabled = false;
            filterSubmit.textContent = 'Apply filters';
          }
        });
    }

    libraryFilterForm.addEventListener('submit', function (e) {
      e.preventDefault();
      var params = new URLSearchParams(new FormData(libraryFilterForm));
      var url = libraryFilterForm.action + (params.toString() ? '?' + params.toString() : '');
      applyLibraryFilters(url, true);
    });

    window.addEventListener('popstate', function () {
      applyLibraryFilters(window.location.href, false);
    });
  }

  /* ----------------------------------------------- Google Drive status */

  function setDriveDot(dot, color) {
    ['bg-muted', 'bg-success', 'bg-primary', 'bg-error'].forEach(function (className) {
      dot.classList.remove(className);
    });
    dot.classList.add(color);
  }

  function checkDriveStatus() {
    var panel = document.querySelector('[data-drive-status]');
    if (!panel) return;
    var message = panel.querySelector('[data-drive-status-message]');
    var dot = panel.querySelector('[data-drive-status-dot]');
    var login = panel.querySelector('[data-drive-login]');
    var activity = panel.querySelector('[data-drive-activity]');
    var activityMessage = panel.querySelector('[data-drive-activity-message]');
    var progress = panel.querySelector('[data-drive-progress]');
    var progressText = panel.querySelector('[data-drive-progress-text]');

    panel.classList.remove('hidden');
    panel.classList.add('flex');
    setDriveDot(dot, 'bg-primary');
    fetch('/drive/status')
      .then(function (response) {
        if (!response.ok) throw new Error('status request failed');
        return response.json();
      })
      .then(function (data) {
        var driveStatus = data.status;
        var driveActivity = data.activity || {};
        var active = ['syncing', 'deleting'].indexOf(driveActivity.status) !== -1;
        var authRequired = driveStatus === 'auth_required' || driveActivity.status === 'auth_required';
        var activityProgress = Math.max(0, Math.min(100, Number(driveActivity.progress) || 0));

        message.textContent = data.message || driveActivity.message || 'Google Drive status unavailable.';
        activity.classList.toggle('hidden', !active);
        activity.classList.toggle('flex', active);
        if (active) {
          setDriveDot(dot, 'bg-primary');
          message.classList.add('hidden');
          activityMessage.textContent = driveActivity.message || 'Working with Google Drive...';
          progress.style.width = activityProgress + '%';
          progressText.textContent = activityProgress + '%';
        } else if (driveStatus === 'connected') {
          setDriveDot(dot, 'bg-success');
          message.classList.remove('hidden');
          message.textContent = 'Google Drive Synced';
        } else if (authRequired) {
          setDriveDot(dot, 'bg-primary');
          message.classList.remove('hidden');
          message.textContent = 'Google Drive authentication required';
          var target = new URL(login.href, window.location.origin);
          target.searchParams.set('next', window.location.pathname + window.location.search);
          login.href = target.pathname + target.search;
        } else {
          setDriveDot(dot, 'bg-error');
          message.classList.remove('hidden');
          message.textContent = 'Google Drive unavailable';
        }
        login.classList.toggle('hidden', !authRequired);
      })
      .catch(function () {
        setDriveDot(dot, 'bg-error');
        message.classList.remove('hidden');
        message.textContent = 'Could not check Google Drive status.';
        login.classList.add('hidden');
        activity.classList.add('hidden');
        activity.classList.remove('flex');
      })
      .finally(function () { window.setTimeout(checkDriveStatus, 2500); });
  }

  checkDriveStatus();
})();
