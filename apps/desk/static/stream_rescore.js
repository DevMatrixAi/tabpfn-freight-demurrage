/* stream re-score — extracted for density push */
(function(){
  var btn = document.getElementById('btn-stream-rescore');
  var auto = document.getElementById('stream-auto');
  var modeSel = document.getElementById('stream-mode');
  var timer = null;
  var busy = false;

  function syncTicker(board){
    if(!board) return;
    var dollars = document.getElementById('ticker-dollars');
    var rows = document.getElementById('ticker-rows');
    if(dollars && board.dataset.demurrage != null){
      var n = Number(board.dataset.demurrage);
      dollars.textContent = '$' + n.toLocaleString(undefined, {maximumFractionDigits:0});
    }
    if(rows && board.dataset.nRows != null){
      rows.textContent = board.dataset.nRows;
    }
  }

  async function streamRescore(){
    if(busy) return;
    busy = true;
    if(btn){ btn.disabled = true; btn.textContent = 'Re-scoring…'; }
    try {
      var mode = modeSel ? modeSel.value : 'mock';
      var body = new URLSearchParams({mode: mode, count: '1', partial: '1'});
      var res = await fetch('/stream-rescore', {
        method: 'POST',
        headers: {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'text/html'},
        body: body,
        credentials: 'same-origin'
      });
      if(!res.ok) throw new Error('HTTP ' + res.status);
      var html = await res.text();
      var tmp = document.createElement('div');
      tmp.innerHTML = html.trim();
      var neu = tmp.querySelector('#live-board') || tmp.querySelector('#risk-board') || tmp.firstElementChild;
      var cur = document.getElementById('live-board') || document.getElementById('risk-board');
      if(neu && cur){
        cur.replaceWith(neu);
        syncTicker(document.getElementById('live-board') || document.getElementById('risk-board'));
      }
    } catch(err){
      console.error(err);
      var st = document.getElementById('stream-status');
      if(st) st.innerHTML = '<span class="warn-banner">Stream re-score failed: ' + err.message + '</span>';
    } finally {
      busy = false;
      if(btn){ btn.disabled = false; btn.textContent = 'Stream event + re-score'; }
    }
  }

  if(btn) btn.addEventListener('click', streamRescore);
  if(auto){
    auto.addEventListener('change', function(){
      if(timer){ clearInterval(timer); timer = null; }
      if(auto.checked){ timer = setInterval(streamRescore, 5000); streamRescore(); }
    });
  }
})();
