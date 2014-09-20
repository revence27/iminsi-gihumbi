		function start() {
				myform.ca.checked = true;
				myform.cb.checked = true;
				myform.cc.checked = true;
				myform.provchoose.disabled = false;
				myform.distchoose.disabled = false;
				myform.locchoose.disabled = false;
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
				
				