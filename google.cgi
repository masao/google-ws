#!/usr/local/bin/ruby
# -*- Ruby -*-

$:.unshift "."
require 'google'

GC.disable

ID = '$Id$'

GOOGLE_WSDL = 'http://api.google.com/GoogleSearch.wsdl'

TERM_WSDL = {
   'edr' => TermWSDL::new("EDR", 'http://nile.ulis.ac.jp/~masao/term-viz-ws/edr/term.wsdl'),
   'odp' => TermWSDL::new("ODP", 'http://nile.ulis.ac.jp/~masao/term-viz-ws/odp/term.wsdl')
}

cgi = CGI.new

begin
	if cgi.valid?( 'key' ) then
		google = GoogleCGI::GoogleSearch::new( cgi, "./skel/google-search.rhtml" )
	elsif cgi.valid?( 'dummy' ) then
		google = GoogleCGI::GoogleDummy::new( cgi, "./skel/google.rhtml" )
	else
		google = GoogleCGI::GoogleForm::new( cgi, "./skel/google.rhtml" )
	end

	print cgi.header( 'text/html; charset=utf-8' )
	print google.eval_rhtml

rescue Exception
	print "Content-Type: text/plain\n\n"
	puts "#$! (#{$!.class})"
	puts ""
	puts $@.join( "\n" )
end
