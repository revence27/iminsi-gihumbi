		function start() {
				myform.ca.checked = false;
				myform.cb.checked = false;
				myform.cc.checked = false;
				myform.provchoose.disabled = true;
				myform.distchoose.disabled = true;
				myform.locchoose.disabled = true;
				}
				onload = start;
				function chgtx() {
					myform.provchoose.disabled = !myform.ca.checked;
					}
				function chgty() {
					myform.distchoose.disabled = !myform.cb.checked;
					}
				function chgtz() {
					myform.locchoose.disabled = !myform.cc .checked;
					}
				
				