// Generated by CoffeeScript 1.6.3
var condenseNavBar, deleteableColumns, jigTheElements, participatingTable;

$(function() {
  var clt;
  clt = new ClientSide(document);
  clt.activateDates('activedate');
  deleteableColumns();
 // condenseNavBar('.collapsiblenav');
  return participatingTable('.participant');
});

participatingTable = function(seeker) {
  var cell, clink, curlk, ncell, pcs, pn, row, tbl, td, thelnk, tr, _i, _len, _ref, _results;
  tbl = $(seeker);
  curlk = document.location.toString();
  pcs = curlk.split('?')[1] || '';
  _ref = $('tr', tbl);
  _results = [];
  for (_i = 0, _len = _ref.length; _i < _len; _i++) {
    tr = _ref[_i];
    row = $(tr);
    _results.push((function() {
      var _j, _len1, _ref1, _results1;
      _ref1 = $('td', row);
      _results1 = [];
      for (_j = 0, _len1 = _ref1.length; _j < _len1; _j++) {
        td = _ref1[_j];
        cell = $(td);
        pn = cell.attr('partname');
        if (pn != null) {
          ncell = $('<td></td>');
          ncell.addClass('goodtot');
          clink = $('<a>…</a>');
          thelnk = "" + pcs + "&subcat=" + pn;
          clink.attr('href', "/tables/reports?" + thelnk);
          ncell.append(clink);
          cell.before(ncell);
          _results1.push($.ajax("/data/reports?" + thelnk, {
            context: clink,
            success: function(dat, stt, xhr) {
              return this.text(dat['total']);
            }
          }));
        } else {
          _results1.push(void 0);
        }
      }
      return _results1;
    })());
  }
  return _results;
};

condenseNavBar = function(seeker) {
  var nav, nnv;
  nav = $(seeker);
  nnv = $('<a class="navholder">Show Navigation</a>');
  nnv.hide();
  nnv.click(function() {
    return nnv.hide('fast', function() {
      return nav.show('fast');
    });
  });
  nav.parent().append(nnv);
  return nav.hide('slow', function() {
    return nnv.show();
  });
};

jigTheElements = function(sel, deg) {
  var cur, dem, got, it, _i, _len, _results;
  dem = $(sel);
  _results = [];
  for (_i = 0, _len = dem.length; _i < _len; _i++) {
    it = dem[_i];
    got = $(it);
    cur = (deg / 2) - Math.floor(Math.random() * deg);
    _results.push(got.css('transform', "rotate(" + cur + "deg)"));
  }
  return _results;
};

deleteableColumns = function() {
  var hd, i, t, td, _i, _len, _ref, _results;
  _ref = $('.largetable thead th');
  _results = [];
  for (i = _i = 0, _len = _ref.length; _i < _len; i = ++_i) {
    t = _ref[i];
    td = $(t);
    hd = $('<a class="hider" href="javascript://dio.1st.ug/">x</a>');
    hd.attr('title', "Hide the '" + (td.text()) + "' column");
    hd.attr('colpos', i);
    hd.click(function(evt) {
      var c, pos, r, sth, tbl, thd, x, _j, _k, _len1, _len2, _ref1, _ref2;
      sth = $(evt.target);
      pos = parseInt(sth.attr('colpos'));
      thd = sth.parent();
      tbl = thd.parent().parent().parent();
      _ref1 = $('tr', tbl);
      for (_j = 0, _len1 = _ref1.length; _j < _len1; _j++) {
        r = _ref1[_j];
        _ref2 = $('td', r);
        for (x = _k = 0, _len2 = _ref2.length; _k < _len2; x = ++_k) {
          c = _ref2[x];
          if (pos === x) {
            $(c).hide('fast');
          }
        }
      }
      return thd.hide();
    });
    td.append(' ');
    _results.push(td.append(hd));
  }
  return _results;
};